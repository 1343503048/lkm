# sched/fair: remove quota/burst write-order dependency

## TL;DR

CFS 带宽的 `cpu.max` 与 `cpu.max.burst` 目前写入顺序敏感：quota 无限时配了大 burst，之后写有限 quota 会 EINVAL；先增 burst 再增 quota 同样失败。Zhe Liu 的 v2（3 补丁）改成「配置的 burst 与当前 quota 解耦，在 refill 时钳到 `quota + min(burst, quota)`」，并补两种写入顺序的 selftest 与 v1/v2 文档。本日 Tao Cui 跑通了 selftest 并指出 v2 丢掉的求和上界检查会导致 `u64` 回绕成 0，需要 v3 修正。

## 背景与问题

`tg_set_bandwidth()` 在写入时会把已配置的 burst 与新 quota 一起校验：

- quota 无限时先配 burst：`echo 100000000 > cpu.max.burst` 后 `echo "50000 100000" > cpu.max` 直接 `Invalid argument`，quota 保持无限，唯一恢复办法是用户态知道要先清 burst；cgroup v1 的 `cpu.cfs_quota_us` 同样受影响。
- 两者同时上调时，先写 burst 会拿旧 quota 校验而 EINVAL。

v1 的做法是「写 quota 时把不兼容的 burst 重置为 0」。Michal Koutný（SUSE，cgroup 侧）不接受：`"Why not clamp the burst_us to quota_us? That's quite natural to me. ... the user configured values should not get lost, the resulting burst value (0 or quota or whatever makes sense) might be applied effectively (to allow configuration order independence) but not overwrite what was configured."`（并转述了 sashiko 的同一意见）。因此 v2 改为保留配置值、在执行侧钳制。

## 技术方案

- `kernel/sched/core.c` `tg_set_bandwidth()`：去掉 `burst_us > quota_us || burst_us + quota_us > max_bw_runtime_us` 这条与当前 quota 耦合的校验，只保留 `burst_us > max_bw_runtime_us`。
- `kernel/sched/fair.c` `__refill_cfs_bandwidth_runtime()`：`cfs_b->runtime = min(cfs_b->runtime, cfs_b->quota + min(cfs_b->burst, cfs_b->quota))`，即在补充运行时间时施加相对 quota 的钳制。
- 配置的 `cpu.max.burst` / `cpu.cfs_burst_us` 读回值不变（不再被静默清零），钳制只作用于生效值。
- 补丁 2/3 在 `tools/testing/selftests/cgroup/test_cpu.c`（+40 行）覆盖两种写入顺序；补丁 3/3 更新 `Documentation/admin-guide/cgroup-v2.rst` 与 `Documentation/scheduler/sched-bwc.rst` 说明顺序无关行为。
- 补丁 1/3 带 `Fixes: f4183717b370`（"sched/fair: Introduce the burstable CFS controller"）与 `Cc: stable@vger.kernel.org`。总规模 5 文件、59 行新增 / 13 行删除。

## 版本演进与当前进展

- v1（08-20，2 补丁，`sched/fair: Reset incompatible burst on quota change`）：写 quota 时把不兼容 burst 归零，附 v2 selftest 与文档。
- 08-20 Michal Koutný 建议改为钳制且不得覆盖用户配置值；08-26 作者回帖明确 v2 计划（去掉 burst 与当前 quota 的耦合校验、refill 时 `min(burst, quota)` 钳制、保留读回值），并称已在 next-20260824 上测过两种写入顺序。
- v2（本日，3 补丁，`20260904062013.504236-1-liuzhe1@kylinos.cn`）：按上述方向重做，新增「burst-first 增加」这一第二种顺序的 selftest，文档一并更新。
- 09-04 Tao Cui 在 next-20260903 的 VM 里跑 selftest：打上系列后 `test_cpu` 全部 10 个用例通过，未打补丁的 `test_cpucg_max_burst` 失败（说明测试确实抓到了旧行为），给出 `Tested-by`；同时指出丢掉求和检查不安全。本日匹配 3 封邮件，v3 尚未发出（缓存中未获取到）。

## Maintainer 意见与讨论焦点

**Michal Koutný（SUSE，cgroup 侧，v1 的关键意见）**：反对「重置为 0」，主张钳制，且明确要求用户配置的 burst 值不能被内核改写——v2 的整个设计由此而来。

**Tao Cui（linux.dev / kylinos，本日 17:21，给出 Tested-by）**：
- 验证：next-20260903 的 VM 中，`test_cpu` 10 个用例全通过；未打补丁时 `test_cpucg_max_burst` 失败。
- 提出阻塞性 bug（他注明由自动溢出检查工具 sashiko 先发现、自己重算了算术）：删掉 `burst_us + quota_us <= max_bw_runtime_us` 检查不安全。当 quota 与 burst 都接近 `MAX_BW` 时，`sched_cfs_period_timer()` 的 period 伸缩路径会把两者一起倍增，最多 512 倍，于是 v2 新加的钳制 `quota + min(burst, quota)` 在 `u64` 上回绕成 0，该组每次 refill 都拿到 0 运行时——即被彻底饿死。
- 给出具体修法：只删 `burst_us > quota_us` 这一项比较，保留求和检查；两种写入顺序仍然通过（举便：burst=80ms、quota=50ms 时总和 130ms，远低于上限）。

**讨论焦点**：方向上已无分歧（配置值保留 + 生效时钳制），争的是实现细节的边界安全；此外 sashiko 自动检查器在本系列两次介入（v1 与 v2），是本线程事实上的第二 reviewer。缓存中未见 Peter Zijlstra / Tejun Heo 等调度器或 cgroup 主要维护者的表态。

## 合入评估

likelihood: **possible**。

依据：这是有 `Fixes:` 与 `Cc: stable` 的行为修复，解决的是用户态可复现的配置顺序坑；方向已被 cgroup 侧 reviewer 认可并落成 v2；selftest 与文档齐全，且已有 `Tested-by`。

卡点（明确且已定位）：
- v2 丢掉 `burst_us + quota_us > max_bw_runtime_us` 校验引入 `u64` 回绕，period 倍增路径下可导致该组 refill 恒为 0——这是比原 bug 更严重的后果，必须先修。
- 修法是现成的（只删 `burst_us > quota_us`、保留求和检查），但需要作者发 v3 并复核「burst-first / quota-first」两种顺序在新组合校验下仍全部通过。
- 缓存中未见调度器维护者对本系列的 Acked-by 或排队动作。

## 效果评估

邮件中未提供性能/吞吐数据，本系列属接口行为修复。可用的验证证据：

- v2 changelog 记录的测试方式：`make -C tools/testing/selftests TARGETS=cgroup`。
- Tao Cui 的实测：next-20260903 VM 中，打过系列后 `test_cpu` 全部 10 个用例通过；未打补丁的内核上 `test_cpucg_max_burst` 失败，证明新增用例能捕获旧的顺序依赖行为。
- 作者在 08-26 的回帖中称已在 next-20260824 上测过两种写入顺序。
- 未提供：`u64` 回绕场景的实际复现数据（Tao Cui 是算出来的，邮件中未附实验），以及 burst 生效后对 throttling 统计的影响。

## 我可以参与的点

- **可直接代验的修正**：按 Tao Cui 的方案出一版 `tg_set_bandwidth()`（只删 `burst_us > quota_us`、保留 `burst_us + quota_us > max_bw_runtime_us`），并补一个极端用例：quota/burst 同时接近 `MAX_BW`，再强制 `sched_cfs_period_timer()` 多次倍增 period，断言 `cfs_b->runtime` 不为 0。这类「溢出边界」用例目前系列里缺，是很好的介入点。
- **语义复核点**：`__refill_cfs_bandwidth_runtime()` 里的钳制在 quota 被动态改小时是否会让已积累的 burst 余额一次性被砍掉（`min(runtime, quota + min(burst, quota))` 在 refill 时刻生效），以及 `cpu.max.burst` 读回值与 `nr_burst`/`burst` 统计是否仍自洽。
- **容器场景价值**：写入顺序敏感对 K8s / Docker 这类分两步写 `cpu.max` 与 `cpu.max.burst` 的管理面是实打实的坑。可以把麒麟/K8s 侧的写入序列整理成回归用例贡献到 `test_cpu.c`，并回帖说明该修复对容器运行时的必要性（有利于推动 stable 合入）。
- **回合评估**：OLK-6.6 若已启用 CFS burst（`cpu.max.burst`），这个顺序依赖同样存在，且修复面很小、适合先行回合到内部树并补 stable 跟踪。

## 参考链接

- 邮件线程：
  - v2 cover letter: <https://lore.kernel.org/all/20260904062013.504236-1-liuzhe1@kylinos.cn/>
  - v2 1/3: <https://lore.kernel.org/all/20260904062013.504236-2-liuzhe1@kylinos.cn/>
  - Tao Cui 的 Tested-by 与溢出问题报告: <https://lore.kernel.org/all/ce007c25-8d49-4df4-9508-3af911f90eb7@linux.dev/>
  - Michal Koutný 对 v1 的意见: <https://lore.kernel.org/all/aobnZEh1hfIBhswD@localhost.localdomain/>
  - v1 cover letter: <https://lore.kernel.org/all/20260820033218.214259-1-liuzhe1@kylinos.cn/>
- 相关代码/commit：
  - `kernel/sched/core.c` `tg_set_bandwidth()`
  - `kernel/sched/fair.c` `__refill_cfs_bandwidth_runtime()` / `sched_cfs_period_timer()`
  - `Fixes: f4183717b370` ("sched/fair: Introduce the burstable CFS controller")
  - `tools/testing/selftests/cgroup/test_cpu.c`

---
id: sched-20260904-004
date: '2026-09-04'
subject: 'sched/fair: remove quota/burst write-order dependency'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: 20260904062013.504236-1-liuzhe1@kylinos.cn
lore_url: https://lore.kernel.org/all/20260904062013.504236-1-liuzhe1@kylinos.cn/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Zhe Liu
maintainers_involved:
- Michal Koutný
- Tao Cui
patch_series:
- 'sched/fair: Remove the write-order dependency between cpu.max and cpu.max.burst'
- 'selftests: cgroup: Test CPU quota and burst write order'
- 'Documentation: describe CPU quota and burst ordering'
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 删掉 burst_us + quota_us <= max_bw_runtime_us 校验后，period 倍增路径下 quota + min(burst, quota) 会 u64 回绕为 0，导致该组 refill 恒得 0 运行时
  - 需要发 v3 只删 burst_us > quota_us 一项比较并保留求和检查
  - 缓存中未见调度器/cgroup 主要维护者的 Acked-by 或排队动作
  next_action: 作者发 v3：保留 max_bw_runtime_us 求和校验，并补一个 quota/burst 同时接近 MAX_BW 且 period 多次倍增的边界用例。
contribution_opportunities:
- 实现并验证 Tao Cui 提出的 v3 校验组合（只删 burst_us > quota_us，保留求和检查）
- 补 quota/burst 接近 MAX_BW + period 倍增的 u64 溢出回归用例
- 复核 quota 动态改小时 refill 钳制对已积累 burst 余额的影响
- 把容器运行时（K8s/Docker）两步写 cpu.max 的真实序列整理进 test_cpu.c
source_email_count: 3
related_articles: []
tags:
- sched/fair
- cgroup
---
