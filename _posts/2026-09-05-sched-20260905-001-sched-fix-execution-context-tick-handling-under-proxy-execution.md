---
id: sched-20260905-001
date: '2026-09-05'
subject: 'sched: Fix execution-context tick handling under proxy execution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260904085244.799276-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20260904085244.799276-1-sh_def@163.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: '2026-09-07'
authors:
- Hui Su
maintainers_involved:
- Tim Chen
- Chen Yu
patch_series:
- 'sched/numa: Drive NUMA task tick from execution context'
- 'sched/cache: Drive cache task tick from execution context'
merge_assessment:
  likelihood: high
  blocking_issues:
  - Chen Yu 承诺的测试结果尚未回帖
  - Reviewed-by 只打在 v3 1/2 上，2/2 无独立 tag
  - sched_tick_exec_ctx() 放 core.c 还是 fair.c 并导出的 nit 可能引出 v4
  - 代理执行下 task_tick_core() 切片消耗失效是遗留 bug，需另开系列
  next_action: 等 v4 或合入；跟进 task_tick_core() 独立修复是否成帖
contribution_opportunities:
- 回帖支持 pick 时刻 task-clock 基线（5985/5985 与旧判定一致）而非 vruntime 基线
- 在 SCHED_PROXY_EXEC + SCHED_CORE + force-idle 环境复现 donor 切片永不消耗
- 复核 sched_tick() 与 sched_tick_remote() 两处 helper 调用顺序一致性
source_email_count: 5
related_articles:
- sched-20260904-001
- sched-20260903-001
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
title: 'sched: Fix execution-context tick handling under proxy execution'
layout: article
---

## TL;DR

Hui Su 的 2 补丁系列把 NUMA / cache 的 task tick 从调度上下文（`rq->donor`）改挂到执行上下文（`rq->curr`），使 fair 任务替 RT/deadline donor 代理执行时 `task_tick_numa()` / `task_tick_cache()` 仍能运行。v3（09-04 发出）已在 09-05 拿到 Tim Chen 的 `Reviewed-by`，Chen Yu 表态「两个补丁都没问题」并在跑验证；同日讨论重点已转移到被本系列明确拆出去的另一条 bug——代理执行下 `task_tick_core()` 的切片消耗判定失效。

## 背景与问题

代理执行把调度上下文与执行上下文拆开：`rq->donor` 是拿到 CPU 的那个调度上下文，`rq->curr` 是真正在跑的任务。`sched_tick()` 通过 `rq->donor` 派发调度类的 task tick，而 NUMA 与 cache 的 tick 消费的是执行上下文的状态（任务本身、`curr->mm`、`curr->se.sum_exec_runtime`）。结果是 fair 任务替 RT/dl donor 代理执行时，这两个 hook 一次都不会被调用：NUMA hint fault 扫描不推进、cache 扫描的 mm epoch 不更新。Chen Yu 在 09-03 的回帖里补充了准确的根因表述，并指出这与 Prateek Nayak 更早提出的「要用 `rq->curr->mm`」是同一件事。

## 技术方案

- v2 起把 NUMA / cache 的执行上下文 tick 处理从 `task_tick_fair()` 上移到 `sched_tick()`，判据改为「`rq->curr` 属于 fair class」，因此 donor 属于其他调度类时 hook 也能跑；并在 `sched_tick_remote()` 里补同样调用以保持 full-dynticks 行为。
- v3 把两处逻辑收敛成公共 helper `sched_tick_exec_ctx()`，让 `sched_tick()` 与 `sched_tick_remote()` 不会漂移；`sched_tick_remote()` 原有基于 curr 的调度类分派保持不变，helper 在其后调用。
- 同时在 commit message 里说明 misfit / overutilized / core-scheduling 的 tick 处理为何仍留在调度上下文侧。
- 改动量很小：`kernel/sched/core.c` +15、`kernel/sched/fair.c` 18 行改动、`kernel/sched/sched.h` +2（26 insertions / 9 deletions）。

## 版本演进与当前进展

- v1（09-02）→ v2（09-03）：从 `task_tick_fair()` 移到 `sched_tick()`，判据换成 curr 的调度类，补 `sched_tick_remote()`。
- v2 → v3（09-04）：抽出 `sched_tick_exec_ctx()`；重写 NUMA 侧 rationale（执行上下文状态与其 task/mm，`sum_exec_runtime` 只是支持性论据）；把 review 中冒出来的 `task_tick_core()` 切片统计问题明确留在系列之外。
- 09-05 状态：v3 已获 Tim Chen `Reviewed-by`，Chen Yu 称跑完测试回报，截至当日正文里没有该测试结论。系列本身接近可合入。
- 与 [[sched-20260904-001]] / [[sched-20260903-001]] 为同一系列的不同版本记录。

## Maintainer 意见与讨论焦点

- **Tim Chen（Intel）**，09-05 在 v3 1/2 上：唯一的 nit 是「可以考虑把 `sched_tick_exec_ctx()` 放到 fair.c 里并导出，这样 `task_tick_numa()` 和 `task_tick_cache()` 能保持 static」，随即补充「两边都行，无所谓」；然后给出「Otherwise the two patches in the series look good to me. **Reviewed-by:** Tim Chen」。
- **Chen Yu（Intel）**，09-04 在 v3 上：「Both patches look good to me, let me launch a test and verify it works as expected and report back later」——09-05 未见回报。更早他在 v2 上已说「This fix looks good to me」，并追问改用 vruntime 后判定被收紧的问题。
- **真正的分歧点在系列之外**：Tim Chen 09-04 指出 `task_tick_core()` 必须继续跟着 donor（切片属于调度上下文），但 `__entity_slice_used()` 用 `se->sum_exec_runtime - se->prev_sum_exec_runtime`，代理执行下 donor 的 `sum_exec_runtime` 不推进（`update_se()` 把 runtime 记到 `rq->curr`），force-idle 重调度可能永远不触发；并给出用 vruntime/deadline 反推的第一版原型。Hui Su 09-04 实测证伪：`update_curr()` 后 `update_deadline()` 已推进 deadline，重建出的 `vused` 只有十万量级（`vslice` = 2100000），`used` 仍为 0。
- Tim Chen 09-05 承认该反例并给出第二版原型：给 `struct sched_entity` 增加 `core_slice_vruntime`，在 `set_next_entity()` 记录 pick 时刻的 vruntime 基线，`vused = se->vruntime - se->core_slice_vruntime`、`vslice = calc_delta_fair(se->slice, se)`。
- Hui Su 09-05 又测出第二版原型的边界问题：在 `CONFIG_FAIR_GROUP_SCHED` + 嵌套 cgroup 的只观测实验里，11 轮共 5985 个 non-proxy 采样中 29 个属于「pick 之后 `sched_entity` 被 reweight」，其中 4 个 vruntime 判定与现有判定不一致，而基于 task-clock 的判定与现有判定 5985 采样全部一致；他给出一条因果 trace（`pick_hweight=1048576` → `current_hweight=15138`，`vused=7980540` / `vslice=145462386` → used=0，而现有判定 used=1），原因是 `vused` 是 pick 基线以来按旧权重累积的服务量，`vslice` 却按当前权重换算，两者尺度不再一致。
- 结论：执行上下文本身这 2 个补丁已收敛；代理执行下的 force-idle 切片统计是尚未提补丁的独立 bug，目前只有两版原型和实测反证。

## 合入评估

**likelihood: likely。**

依据：Intel 两位 NUMA/cache 相关维护者同时正面表态，其中 Tim Chen 已给 `Reviewed-by`；改动小（+26/-9）、限定在 `CONFIG_SCHED_PROXY_EXEC` 与 nohz_full 远程 tick 路径；v1→v3 的反馈全部落地；review 中挖出的更大问题被明确拆到系列之外，不会反过来卡住本系列。

卡点：Chen Yu 承诺的测试结果到 09-05 还没回帖；`Reviewed-by` 打在 1/2 上、2/2 尚无独立 tag；`sched_tick_exec_ctx()` 放 core.c 还是 fair.c 的 nit 可能引出 v4；本系列合入后 proxy 下 `task_tick_core()` 失效仍是遗留 bug（需要 Hui Su 说的「另开一线」）。

## 效果评估

无性能数据，v3 cover 给的是功能性验证：`CONFIG_SCHED_PROXY_EXEC=y` 下覆盖 NUMA/cache 四种组合，做了 W=1 对象构建、完整 bzImage/modules 构建，并单独构建启动 `CONFIG_NO_HZ_FULL=y`；QEMU（11.1.0，暴露两个 L3 域）proxy-mutex 复现表明未打补丁内核在代理执行期间完全不调用 `task_tick_numa()` / `task_tick_cache()`，打上后两个 hook 都以 `rq->curr` 被反复调用而 `rq->donor` 仍是 RT 调度上下文，NUMA task work 入队、cache 的 mm scan epoch 推进，3 个 proxy episode 完整跑完，nohz_full CPU 1 的远程 tick 路径确认进入 `sched_tick_exec_ctx()`，无 warning/oops。插桩与复现器刻意排除在系列之外。

## 我可以参与的点

- 接手那条被拆出去的 bug：现有 task-clock 基线在 Hui Su 的数据里 5985/5985 与旧判定一致，而 pick-time vruntime 基线在 reweight 后偏离——这足以支撑一条「别用 vruntime，用 pick 时刻的 `sum_exec_runtime`/task clock」的回帖，作者明确说过欢迎这类反馈。
- 在带 `CONFIG_SCHED_PROXY_EXEC` + `CONFIG_SCHED_CORE` + force-idle 的机器上复现 donor 切片永不消耗、兄弟核无法结束 force-idle 的现象，这是目前缺的直接证据。
- 复核 `sched_tick_exec_ctx()` 在 `sched_tick()` 与 `sched_tick_remote()` 两处的调用顺序是否真的一致（v3 的 factor 动机就是防漂移）；以及它对 `CONFIG_SCHED_SMT` 的 misfit/overutilized 路径「保留在调度上下文」的注释是否与实际代码相符。
- 与 cpuset/cgroup 的交叉点：Hui Su 的 reweight 实验用嵌套 cgroup 改层级权重，正对应用户日常场景；若要在 OLK-6.6 回合 proxy execution，这条 tick 修正和 `task_tick_core()` 遗留 bug 都要一并记账。

## 参考链接

- 相关文章/系列：
  - [[sched-20260904-001]] 同系列 v3 记录。
  - [[sched-20260903-001]] 同系列 v2。
- v3 cover letter：https://lore.kernel.org/all/20260904085244.799276-1-sh_def@163.com/
- v3 1/2 / 2/2：https://lore.kernel.org/all/20260904085244.799276-2-sh_def@163.com/ 、https://lore.kernel.org/all/20260904085244.799276-3-sh_def@163.com/
- Tim Chen 的 Reviewed-by 与 nit：https://lore.kernel.org/all/84f83c4dab930ff41cafbe614bbfa866003caa21.camel@linux.intel.com/
- Chen Yu「跑测试后回报」：https://lore.kernel.org/all/aprpNg3a6fAm8Wdc@fengwei-dev/
- Tim Chen 的 pick 时刻 vruntime 原型：https://lore.kernel.org/all/0d6117e597e6ca3ab3179c6304d6e5e454f53759.camel@linux.intel.com/
- Hui Su 的 reweight 实测反驳：https://lore.kernel.org/all/20260905135843.2818510-1-sh_def@163.com/
- Chen Yu 关于 `task_tick_core()` 的追问：https://lore.kernel.org/all/aprtc9-xD2qCZeW0@fengwei-dev/
- v2 cover（含 v1 链接）：https://lore.kernel.org/all/20260903041154.2479761-1-sh_def@163.com/
- Prateek Nayak 更早的执行上下文建议（Chen Yu 在正文中引用）：https://lore.kernel.org/all/78c81f74-7b27-4f28-9ca2-0d1e27ed9c56@amd.com/
- 相关代码：
  - `kernel/sched/core.c` `sched_tick()` / `sched_tick_remote()` / `sched_tick_exec_ctx()`
  - `kernel/sched/fair.c` `task_tick_numa()` / `task_tick_cache()` / `__entity_slice_used()`
