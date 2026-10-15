# sched/eevdf: Remove redundant RUN_TO_PARITY check

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261012-005：Elif Topuz 提交 EEVDF 小清理——`update_protect_slice()` 只在 `RUN_TO_PARITY` 特性开启时被调用，函数内部的 `sched_feat(RUN_TO_PARITY)` 判断冗余，直接改 `cfs_rq_min_slice()`；Vincent Guittot 当日 `Reviewed-by`。
- sched-20261015-028（今天）：tip-bot2 确认已合并进 tip 的 **sched/core** 分支（Commit-ID `b0f1d7a34d3099973f1ba45d1ce6f36578e510a2`）。

## 背景与问题
（承接 20261012-005）`update_protect_slice()` 唯一调用点 `wakeup_preempt_fair()` 已被 `RUN_TO_PARITY` 特性门控，函数内部再用 `sched_feat(RUN_TO_PARITY)` 决定 slice 取值，内层判断恒真，属死分支。

## 技术方案
（承接 20261012-005）删除内层 `if (sched_feat(RUN_TO_PARITY))`，`slice` 直接取 `cfs_rq_min_slice(cfs_rq)`（`kernel/sched/fair.c` +2/−7），语义无变化。今日合入 tip/sched/core，Committer Peter Zijlstra（Intel），带 Vincent Guittot 的 Reviewed-by。

## 版本演进与当前进展
- v1（2026-10-12，<20261012105001.131311-1-elif.topuz@arm.com>）→ 今日合入 tip/sched/core。

## Maintainer 意见与讨论焦点
Peter Zijlstra 已合并（Committer）；Vincent Guittot Reviewed-by。无遗留分歧。

## 合入评估
*likelihood=merged*。已进 tip/sched/core。*blocking_issues*：无。*next_action*：随 sched/core 进主线（v7.4 周期）。

## 效果评估
无量化数据，纯死分支清理、语义不变。

## 我可以参与的点
当前阶段暂无明显参与空间，已合入 tip。

## 参考链接
- tip-bot2 合并通知：https://lore.kernel.org/all/179205152866.2666988.14970752689594734036.tip-bot2@tip-bot2/
- 原始补丁：https://lore.kernel.org/all/20261012105001.131311-1-elif.topuz@arm.com/
- tip commit：https://git.kernel.org/tip/b0f1d7a34d3099973f1ba45d1ce6f36578e510a2

---
id: sched-20261015-028
date: 2026-10-15
subject: "sched/eevdf: Remove redundant RUN_TO_PARITY check"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261012105001.131311-1-elif.topuz@arm.com>"
lore_url: "https://lore.kernel.org/all/20261012105001.131311-1-elif.topuz@arm.com/"
authors: ["Elif Topuz"]
maintainers_involved: ["Peter Zijlstra", "Vincent Guittot"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261012105001.131311-1-elif.topuz@arm.com>"
    date: 2026-10-12
    summary: "删除 update_protect_slice() 内冗余 RUN_TO_PARITY 分支"
    review_outcome: "Vincent Reviewed-by；Peter 今日合入 tip/sched/core"
upstream_commit: "b0f1d7a34d3099973f1ba45d1ce6f36578e510a2"
fixes_commit: null
merged_branch: "sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/core 进主线（v7.4 周期）"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20261012-005"]
tags: [eevdf]
---