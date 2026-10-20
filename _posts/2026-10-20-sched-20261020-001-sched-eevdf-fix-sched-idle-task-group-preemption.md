---
id: sched-20261020-001
date: 2026-10-20
subject: 'sched/eevdf: Fix sched idle task group preemption'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261019182622.1584454-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20261019181611.1461433-1-vincent.guittot@linaro.org>
  date: 2026-10-20
  summary: 新增 find_matching_se() 向上对齐层级 + wakeup_preempt_sched_idle()，修复扁平层级下 sched_idle
    组未被正确抢占
  review_outcome: Jakub 确认修复 cpu.idle 用例，但指出返回类型应为 enum 且 nice 19 仍回退
- version: v2
  msgid: <20261019182622.1584454-1-vincent.guittot@linaro.org>
  date: 2026-10-20
  summary: 修正 wakeup_preempt_sched_idle() 原型（bool→enum preempt_wakeup_action）并清理未用变量
  review_outcome: 暂无回帖
upstream_commit: null
fixes_commit: 85570f10a4c6
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - nice 19 同 cgroup 回退尚未解决（作者另起补丁排查）
  next_action: v2 待其他维护者确认后合入；作者另发补丁处理 nice 19 回退
contribution_opportunities:
- kind: testing
  description: 验证 cpu.idle 组 wakeup 抢占三路分支及 find_matching_se() 多层嵌套层级对齐
- kind: discussion
  description: 复现并提供不同 cgroup_mode 下 nice 19 的对比数据，助收敛下一轮修复
generated_at: '2026-10-21T01:30:00'
source_email_count: 3
related_articles: []
tags:
- eevdf
- regression
title: 'sched/eevdf: Fix sched idle task group preemption'
layout: article
---

## TL;DR

Vincent Guittot 发往 sched 的单补丁修复：EEVDF「单运行队列」改动（`85570f10a4c6`）后，即使扁平层级把全部 runnable 任务放进同一个 cfs_rq，wakeup 抢占时仍需向上遍历 task group 层级才能判断是否存在 sched_idle 任务组，否则 idle 组任务不会被正确抢占。当日 v1→v2 连发（v2 仅修原型返回类型 + 清理未用变量），Jakub Okoński 实测修复了其 `cpu.idle` 用例但指出「同 cgroup 下 nice 19 spinner 相对 7.2.9 仍回退」，作者明确本补丁只覆盖 sched_idle 组场景、nice 19 另行排查。

## 背景与问题

「sched/eevdf: Move to a single runqueue」系列落地 v7.3 后，社区持续追查调度回归（详见本日 003 增量文章）。Jakub Okoński 报告其 `cpu.idle` cgroup 测试用例出现 wakeup 抢占语义破坏：原实现（单运行队列下扁平层级）把所有 runnable 任务放在同一 cfs_rq，`wakeup_preempt_fair()` 里直接比较 `se_is_idle(se)` 与 `se_is_idle(pse)`，但**没有沿 task group 层级向上找「共同父级的兄弟实体」**，导致 `sched_idle` 任务组不会被非 idle 任务正确抢占（或反向场景误判）。

复现条件：EEVDF 单运行队列 + 带 `sched_idle` 权重的 task group（`cpu.idle` 用例）；症状为 idle 组的 wakeup 抢占行为错误。`Reported-by: Jakub Okoński`，`Fixes: 85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`。

## 技术方案

单补丁（`kernel/sched/fair.c`，+69/-13）：

- 新增 `find_matching_se(&se, &pse)` 辅助函数：把两个 `sched_entity` 先调到同深度、再向上走到「共同父级的兄弟实体」——因为抢占测试只能在同 cfs_rq 的兄弟实体之间进行。
- 新增 `wakeup_preempt_sched_idle(cse, pse)`：调用 `find_matching_se()` 对齐层级后，用 `se_is_idle()` 判定两侧 idle 属性，返回 `PREEMPT_WAKEUP_RESCHED`（idle 让位非 idle）/ `PREEMPT_WAKEUP_NONE`（非 idle 让位 idle）/ `PREEMPT_WAKEUP_PICK`（两侧同类，走原 EEVDF 判定）。
- `wakeup_preempt_fair()` 里原来对 `se/pse` 的 idle 判断替换为调用 `wakeup_preempt_sched_idle()`；非 CONFIG_FAIR_GROUP_SCHED 构建下 `find_matching_se()` 与 `tg_is_idle()` 一样退化为空实现。
- v2 关键改动：`wakeup_preempt_sched_idle()` 的返回类型从 `bool` 改为 `enum preempt_wakeup_action`（作者自述「从二元值改成三元值却忘了改原型」），并清理未用变量。

## 版本演进与当前进展

*current_version: v2*。

- v1（当日，`<20261019181611.1461433-1-vincent.guittot@linaro.org>`）：初始版本，作者随即自回「This was sent too quickly. v2 coming soon」。
- v2（当日，`<20261019182622.1584454-1-vincent.guittot@linaro.org>`）：*changes since v1* — 修正 `wakeup_preempt_sched_idle()` 原型（bool→enum）并清理未用变量。

## Maintainer 意见与讨论焦点

暂无维护者/资深成员对 v2 的正式回帖。作者 Vincent Guittot 本身是 sched 维护者。关键分歧集中在边界：报告人 Jakub Okoński 在 v1 上实测后指出——「你的补丁修好了我的 `cpu.idle` 用例，但（该函数）应返回 `enum preempt_wakeup_action`；且加上这个改动后、在 7.3.0 之上用**同 cgroup 的 nice 19 spinner** 测试，相对 7.2.9 仍回退，我认为这还不完整」。Vincent 回应：「这个补丁只旨在修复 sched_idle 任务组场景，我会另行仔细看 nice 19 场景；你是否已检查过不同 cgroup_mode 下的 nice 19？」——即 nice 19 回退被明确划出本补丁范围。

## 合入评估

*likelihood=high*。作者即调度维护者，修复直指已合入主线的 `85570f10a4c6` 回归、带 `Fixes:` 与 `Reported-by:`，方向无异议。*blocking_issues*：nice 19 同 cgroup 回退尚未解决（作者称另起补丁排查，非本补丁范围）。*next_action*：v2 待其他维护者（Peter Zijlstra 等）确认后合入；作者另发补丁处理 nice 19 回退。

## 效果评估

无量化 benchmark 数字。效果证据来自报告人的功能验证：Jakub Okoński 确认「你的补丁修好了我的 cpu.idle 测试用例」，但 nice 19 场景仍相对 7.2.9 回退（判定为不完整）。属正确性/抢占语义修复，非性能优化。

## 我可以参与的点

- `testing`：在 `CONFIG_FAIR_GROUP_SCHED` 内核上验证 `cpu.idle` 组的 wakeup 抢占（idle→非 idle、非 idle→idle、同类三路分支），并回归 `find_matching_se()` 对多层嵌套 task group 的深度对齐是否正确。
- `discussion`：nice 19 同 cgroup 回退是当前未解决的关键分歧，可复现并提供「不同 cgroup_mode 下 nice 19」的对比数据，帮 Vincent 收敛下一轮修复。

## 参考链接

- v2 patch：https://lore.kernel.org/all/20261019182622.1584454-1-vincent.guittot@linaro.org/
- v1 patch：https://lore.kernel.org/all/20261019181611.1461433-1-vincent.guittot@linaro.org/
- 报告线程（cpu.idle 回归，Jakub Okoński）：https://lore.kernel.org/all/58dc8e8a-7260-43ce-aebb-8d9c29a6afc9@okonski.org/
