# sched/fair: Remove the write-order dependency between cpu.max and cpu.max.burst

## TL;DR

本文为增量更新，完整背景见 [[sched-20260904-004]]（该文以 v2 的 cover 标题 `sched/fair: remove quota/burst write-order dependency` 为题，本篇是 v2 中 1/3 这一补丁本体的标题）。09-07 的进展是决定性的：cpu controller 维护者 Michal Koutný（SUSE）给出 `Reviewed-by`，原话是「The change makes sense to me and it should've been like that from the beginning」，但附带一个必须执行的修改要求——「it may break someone's setup, so I'd take it but revert it should regressions be reported. Hence, I wouldn't mark it for stable.」而作者 v2 里正好带了 `Cc: stable@vger.kernel.org`。他同时否掉了 09-04 Tao Cui 报的那个 u64 溢出：认为那是 sashiko 把 `MAX_BW` 与 `UULONG_MAX`（更准确说是 `UULONG_MAX / NSEC_PER_USEC`）搞混了，并指出这些带 `BW_SHIFT` 的量与 burst 无关，「so even your version should still be safe」。他同时注意到校验实际会被放宽成 `if (burst_us > max_bw_runtime_us / 2) return -EINVAL;` 这种形式。

## 背景与问题

CFS 带宽的 `cpu.max`（quota/period）与 `cpu.max.burst` 目前写入顺序敏感：quota 还是 `max`（无限）时先配一个较大的 burst，之后写有限 quota 会 `EINVAL`；反过来把 quota 与 burst 同时上调时先写 burst 也会因拿旧 quota 校验而失败。根因是 `tg_set_bandwidth()` 把「新配的 burst」与「当前的 quota」耦合校验：

```
if (quota_us != RUNTIME_INF && (burst_us > quota_us ||
				burst_us + quota_us > max_bw_runtime_us))
        return -EINVAL;
```

v1 采取「写 quota 时把不兼容的 burst 清零」，被 Koutný 否决（用户配置值不该被内核改写，应钳制生效值而非改配置值），v2 因此改为「配置的 burst 与当前 quota 解耦，在 `__refill_cfs_bandwidth_runtime()` 里钳到 `quota + min(burst, quota)`」，并补 selftest 与文档。详见 [[sched-20260904-004]]。

## 技术方案

v2 的 1/3 只有 5 增 3 删，两个 hunk：

- `kernel/sched/core.c` `tg_set_bandwidth()`：删掉与当前 quota 耦合的那条复合校验，只保留 `if (burst_us > max_bw_runtime_us) return -EINVAL;`。
- `kernel/sched/fair.c` `__refill_cfs_bandwidth_runtime()`：`cfs_b->runtime = min(cfs_b->runtime, cfs_b->quota + min(cfs_b->burst, cfs_b->quota));`，即生效值相对 quota 钳制，`cpu.max.burst` / `cpu.cfs_burst_us` 的读回值不再被静默改写。

同日讨论中浮现的两个语义点：

1. **校验上界其实变了**：Koutný 顺带注意到，按他的表述这一处「会被放宽成」`if (burst_us > max_bw_runtime_us / 2) return -EINVAL;` 这种形式（他只是在回帖里写出这个式子，没有推导它与本 diff 的对应关系，是否是他期望的最终形态也未有说明）。
2. **加法溢出到底存不存在**：Koutný 认为现有代码里那些带 `BW_SHIFT` 的换算与 burst 无关，sashiko 报的加法溢出是把 `MAX_BW` 与 `UULONG_MAX`（准确说 `UULONG_MAX / NSEC_PER_USEC`）混为一谈，所以「even your version should still be safe」——这直接反驳了 09-04 Tao Cui 的阻塞性结论。

按本地 `kernel/sched` 核对（非邮件内容，供判断谁对谁错用）：`tg_set_bandwidth()` 里有两条不同的界——每条输入值单独要求 `<= U64_MAX / NSEC_PER_USEC`（只为保证换算成 ns 不溢出），而 `max_bw_runtime_us` 定义为 `MAX_BW`（`(1ULL << (64 - BW_SHIFT)) - 1`）；同时 `sched_cfs_period_timer()` 在 period 过短时会把 `period`、`quota`、`burst` 一起乘以 2。也就是说 Koutný 说的「两个量不是一回事」成立，但 `quota + min(burst, quota)` 是否会被后续倍增推到回绕，取决于倍增次数上界，双方邮件里都没有把这段算术写完整——作者的 `Cc: stable` 被要求撤掉之外，这一点仍需要他本人回帖回应。

## 版本演进与当前进展

- 08-20 v1（2 补丁，cover `<20260820033218.214259-1-liuzhe1@kylinos.cn>`，标题 `sched/fair: Reset incompatible burst on quota change`）：写 quota 时归零不兼容 burst；Koutný 反对改写用户配置值。
- 08-26 作者明确 v2 计划：解耦校验、refill 时钳制、保留读回值，并称已在 next-20260824 测过两种写入顺序。
- 09-04 14:20 v2（3 补丁）：1/3 改代码、2/3 加 `tools/testing/selftests/cgroup/test_cpu.c` 两种写入顺序用例、3/3 更新 `Documentation/admin-guide/cgroup-v2.rst` 与 `Documentation/scheduler/sched-bwc.rst`；1/3 带 `Fixes: f4183717b370` 与 `Cc: stable@vger.kernel.org`；系列总规模 5 文件 +59/-13。
- 09-04 17:21 Tao Cui 给出 `Tested-by`（next-20260903 的 VM 里 `test_cpu` 10 个用例全通过、未打补丁时 `test_cpucg_max_burst` 失败），同时报告丢掉求和检查会导致 `quota + min(burst, quota)` 在 u64 上回绕为 0（他注明由 sashiko 先发现、自己重算过算术，并说 period 伸缩路径最多可把两者放大 512 倍），建议只删 `burst_us > quota_us` 而保留求和检查。
- **09-07 22:06 Michal Koutný `Reviewed-by`**：接受改动、要求撤掉 stable 标注（「我会收这个补丁，如果报回退就 revert，因此不要标 stable」）、认为溢出结论不成立。作者当日尚未回帖。
- 截至本日无 v3；缓存中未见 Peter Zijlstra / Ingo Molnar 在本线程的表态，也未见 tip 收树迹象。

## Maintainer 意见与讨论焦点

- **Michal Koutný（SUSE，cgroup cpu controller 维护者）**三件事：
  1. 方向背书：改动合理、本来就该这样，`Reviewed-by`。
  2. 明确的收下条件：撤掉 `Cc: stable`。他的取舍是「可能破坏现有部署 → 收进主线但一旦报回退就 revert，因此不下放 stable」。这对作者是可直接执行的改动，也说明该修复被视为行为变更而非可安全 backport 的 bug fix。
  3. 技术反驳：`BW_SHIFT` 相关换算与 burst 无关，sashiko（以及转述它的 Tao Cui）把 `MAX_BW` 与 `UULONG_MAX / NSEC_PER_USEC` 混淆，因此当前版本仍然安全；同时点出校验形态实际变成 `burst_us > max_bw_runtime_us / 2`。
- **Tao Cui（kylinos / linux.dev）**：目前唯一给出实测验证的人（`Tested-by`，且确认新用例能抓到旧的顺序依赖行为），同时是本线程唯一主张「求和检查必须保留」的人，本日他未再回帖，Koutný 的反驳实际上悬在他头上。
- **讨论焦点**：从「语义该怎样」（已收敛：配置值不动、生效值钳制）转移到「边界安全性 + 是否进 stable」。后者是实际决定合入路径的问题——`Cc: stable` 去留会让这个修复分别走 tip 主线与 stable 树两条完全不同的推广面。
- **未解决**：作者对溢出之争尚未表态；`burst_us > max_bw_runtime_us / 2` 这一形态是否是他有意为之，邮件里也没有说明。

## 合入评估

`likelihood=high`。

依据：cpu controller 维护者已给 `Reviewed-by` 并明确「I'd take it」，只需要把 `Cc: stable` 去掉；方向自 v1 起就没再被质疑；改动体积 5 增 3 删，另有 selftest 与文档；`Fixes: f4183717b370` 明确；还拿到了 `Tested-by`。按 Koutný 的表态，本系列实质上已进入「等作者补一版去掉 stable 标注、由 Peter Zijlstra / 维护者收取」的轨道。

卡点：一是作者需按意见撤掉 `Cc: stable`（v3 或直接带 `Reviewed-by` 重发 1/3）；二是 09-04 报的 u64 回绕争议未闭环——Koutný 认为不存在、Tao Cui 认为存在且给了具体修法，作者若不回应就带着 `Reviewed-by` 提交，容易在维护者侧被再问一次；三是「可能破坏现有部署」这一顾虑本身意味着合入后仍有 revert 风险，尤其是那些依赖「quota 无限时 burst 上界与 quota 相关」这一旧校验语义的管理面；四是本系列尚未获得任何调度器主要维护者的直接表态。

## 效果评估

邮件中没有性能或吞吐数据，本系列属接口行为修复，可用证据是功能性验证：

- Tao Cui（09-04，next-20260903 的 VM）：打系列后 `test_cpu` 全部 10 个用例通过；未打补丁的内核上 `test_cpucg_max_burst` 失败，说明新增用例确实捕获了旧的写入顺序依赖。
- 作者 08-26 称已在 next-20260824 上测过两种写入顺序；v2 cover 记录的测试方式为 `make -C tools/testing/selftests TARGETS=cgroup`。
- 未获取到：u64 回绕的实验复现（Tao Cui 是算术推演，Koutný 的否定同样是算术推演，双方都没跑过极端用例）；burst 生效值被钳制后对 `nr_burst` / `nr_throttled` / `burst_usec` 统计的影响；以及「哪些现有部署会被这个校验放宽影响」的清单。

## 我可以参与的点

- 立刻可做的仲裁实验：把 quota 与 burst 同时设到接近 `MAX_BW`，再人为制造 period 过短让 `sched_cfs_period_timer()` 连续倍增 period/quota/burst，断言 `cfs_b->runtime` 是否回绕为 0。这正是 Koutný 与 Tao Cui 分歧的全部所在，也是本系列目前唯一没人做过的事；一条 selftest 就够，产出比再多的算术推演都有价值。
- 若结论是「安全」，可顺手把 `burst_us > max_bw_runtime_us / 2` 这条 Koutný 点出的实际形态写进提交说明或 `Documentation/scheduler/sched-bwc.rst`，避免用户态按「burst 可等于 max_bw_runtime_us」去配置。
- cpuset/cgroup 生产视角（本方最关心的部分）：这个修复改变的是管理面写入序列的可接受集合。可以把容器运行时（分两步写 `cpu.max` 与 `cpu.max.burst` 的组件）的真实写入序列整理成 selftest 用例，同时回答 Koutný 那句「it may break someone's setup」到底会不会发生——这一份证据也能直接影响是否需要在 `cpu.max.burst` 文档里加「生效值可能被钳到 quota」的显式说明。
- 回合判断：内部树若启用了 CFS burst，这个顺序依赖坑原样存在，且修复面极小（两 hunk、无新增符号），适合先回合到内部基线；但要注意**不要跟 stable**——上游维护者的意图是「主线收、报回退就 revert」，内部回合需要自己承担行为变更风险，建议在内部同时保留「burst 上界与 quota 相关」的回归用例，便于出现回退时快速定位。

## 参考链接

- 本日邮件：
  - Michal Koutný 的 `Reviewed-by` 与不标 stable 的要求：https://lore.kernel.org/all/ap69-MoOmAJifgjG@localhost.localdomain/
- 系列与历史：
  - v2 cover letter：https://lore.kernel.org/all/20260904062013.504236-1-liuzhe1@kylinos.cn/
  - v2 1/3 补丁本体：https://lore.kernel.org/all/20260904062013.504236-2-liuzhe1@kylinos.cn/
  - Tao Cui 的 `Tested-by` 与溢出报告：https://lore.kernel.org/all/ce007c25-8d49-4df4-9508-3af911f90eb7@linux.dev/
  - Koutný 对 v1 的意见（要求钳制而非清零）：https://lore.kernel.org/all/aobnZEh1hfIBhswD@localhost.localdomain/
  - v1 cover letter：https://lore.kernel.org/all/20260820033218.214259-1-liuzhe1@kylinos.cn/
- 相关代码/commit：`kernel/sched/core.c` `tg_set_bandwidth()`；`kernel/sched/fair.c` `__refill_cfs_bandwidth_runtime()` / `sched_cfs_period_timer()`；`tools/testing/selftests/cgroup/test_cpu.c`；`Fixes: f4183717b370`（"sched/fair: Introduce the burstable CFS controller"）
- 相关：[[sched-20260904-004]]

---
id: sched-20260907-008
date: '2026-09-07'
subject: 'sched/fair: Remove the write-order dependency between cpu.max and cpu.max.burst'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260904062013.504236-1-liuzhe1@kylinos.cn>'
lore_url: https://lore.kernel.org/all/20260904062013.504236-2-liuzhe1@kylinos.cn/
upstream_commit: null
fixes_commit: f4183717b370
merged_branch: null
current_version: v2
generated_at: '2026-09-07'
authors:
- Zhe Liu
maintainers_involved:
- Michal Koutný
- Tao Cui
patch_series:
- version: v1
  msgid: '<20260820033218.214259-1-liuzhe1@kylinos.cn>'
  date: '2026-08-20'
  summary: '2 补丁：写 quota 时把与新 quota 不兼容的 burst 重置为 0，附带 selftest。'
  review_outcome: 'Michal Koutný 反对改写用户配置值，主张钳制生效值；作者 08-26 接受并规划 v2。'
- version: v2
  msgid: '<20260904062013.504236-2-liuzhe1@kylinos.cn>'
  date: '2026-09-04'
  summary: '3 补丁中的 1/3：tg_set_bandwidth() 删掉 burst_us > quota_us 与 burst_us + quota_us > max_bw_runtime_us 的耦合校验，只留 burst_us > max_bw_runtime_us；__refill_cfs_bandwidth_runtime() 改为 min(runtime, quota + min(burst, quota))；2/3 补 test_cpu.c 两种写入顺序用例，3/3 更新 cgroup-v2.rst 与 sched-bwc.rst。带 Fixes: f4183717b370 与 Cc: stable。'
  review_outcome: 'Tao Cui 09-04 给出 Tested-by 并报丢掉求和检查后 quota+min(burst,quota) 在 period 倍增路径下可 u64 回绕为 0；Michal Koutný 09-07 给 Reviewed-by，同时要求撤掉 Cc: stable（收但报回退即 revert），并认为溢出是 sashiko 混淆了 MAX_BW 与 UULONG_MAX/NSEC_PER_USEC、当前版本仍然安全。作者尚未回帖。'
merge_assessment:
  likelihood: high
  blocking_issues:
  - '需按 Koutný 意见移除 Cc: stable 标注（v2 带该标签），否则维护者不收'
  - '上一轮 Tao Cui 指出的 u64 回绕争议仍需作者回应，作者本日尚未回帖；Koutný 认为不存在'
  - 'Koutný 明确该改动可能破坏现有部署，收取后若报回退会 revert，合入后仍存在回退风险'
  - '未见 Peter Zijlstra / Ingo Molnar 在本线程表态，也无 tip 收树迹象'
  next_action: '等作者去掉 Cc: stable 并带 Reviewed-by 重发（或直接回一句说明溢出争议结论）；同时关注是否有人把 period 倍增下的极端用例跑出来'
contribution_opportunities:
- kind: testing
  description: '把 quota 与 burst 同时设到接近 MAX_BW、再触发 sched_cfs_period_timer() 连续倍增，实测 quota + min(burst, quota) 是否回绕为 0，直接仲裁 Koutný 与 Tao Cui 的分歧'
- kind: review
  description: '确认校验实际形态为 burst_us > max_bw_runtime_us / 2 是否是有意设计，并建议写进提交说明或 sched-bwc.rst'
- kind: extend
  description: '把容器运行时两步写 cpu.max / cpu.max.burst 的真实序列整理进 test_cpu.c，并评估 burst 被钳制后 nr_burst/nr_throttled/burst_usec 统计是否仍自洽'
- kind: new_patch
  description: '内部基线若启用 CFS burst，可先行回合（两 hunk、无新增符号），但需自担行为变更风险并保留旧校验语义的回归用例，不要跟 stable'
source_email_count: 1
related_articles:
- sched-20260904-004
tags:
- cgroup
- cfs
---
