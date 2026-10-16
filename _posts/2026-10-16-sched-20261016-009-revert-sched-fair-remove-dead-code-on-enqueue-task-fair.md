---
id: sched-20261016-009
date: 2026-10-16
subject: 'Revert "sched/fair: Remove dead code on enqueue_task_fair()"'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261015082919.4344-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20261015082919.4344-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261015082919.4344-1-kayracizmeci@gmail.com>
  date: 2026-10-15
  summary: 恢复 enqueue_task_fair() 的 cfs_rq->curr == se 分支（CFS_BANDWIDTH 场景需要）
  review_outcome: Peter 合入 tip sched/core
upstream_commit: 0a94d0ea8d8b
fixes_commit: 819224e506bc
merged_branch: sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 无（已合入）
contribution_opportunities: []
generated_at: '2026-10-17T01:30:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- regression
title: 'Revert "sched/fair: Remove dead code on enqueue_task_fair()"'
layout: article
---

## TL;DR
先前合入的「sched/fair: Remove dead code on enqueue_task_fair()」（commit 819224e506bc）把 `enqueue_task_fair()` 里 `cfs_rq->curr == se` 分支当死代码删掉了，但该情形在 CFS_BANDWIDTH 下真实存在——任务被 throttle/dequeue 后可在另一 CPU 上 unthrottle 并在 schedule() 前再次 enqueue。Kayra Cizmeci 发 revert 补丁，Peter 已合入 tip sched/core（commit 0a94d0ea8d8b）。

## 背景与问题
原 commit `819224e506bc` 判定 `enqueue_task_fair()` 中 `cfs_rq->curr == se` 不会发生，遂删除该分支。但 `cfs_rq->curr == se` 在 **CFS_BANDWIDTH** 下可真实出现：任务可被 throttle 后 dequeue、在另一 CPU 上 unthrottle、再于 schedule() 之前被 enqueue。删除后该路径缺失 `place_entity()` 处理。由 Christian Loehle 报告。

## 技术方案
revert 补丁（`kernel/sched/fair.c`，+15/−3）：恢复被删的 `curr = (cfs_rq->curr == se)` 判断与 `if (curr) place_entity(cfs_rq, se, flags)`，并把 `reweight_eevdf()/place_entity()/__enqueue_entity()` 包回 `if (!curr)` 块，同时补注释说明 CFS_BANDWIDTH 下该路径发生的机制。

## 版本演进与当前进展
revert 补丁（2026-10-15，<20261015082919.4344-1-kayracizmeci@gmail.com>），2026-10-16 由 Peter 合入 tip sched/core（commit `0a94d0ea8d8b`，committer Peter Zijlstra）。

## Maintainer 意见与讨论焦点
Peter Zijlstra 收取合入；`Reported-by: Christian Loehle`、`Fixes: 819224e506bc`。无分歧。

## 合入评估
*likelihood=merged*。已合入 tip sched/core（commit `0a94d0ea8d8b`）。*blocking_issues*：无。*next_action*：无（已合入）。

## 效果评估
无量化数据；属正确性 revert（恢复 CFS_BANDWIDTH 路径的缺失处理）。

## 我可以参与的点
当前阶段已合入，无明显参与空间。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213767471.2666988.7617836767029075656.tip-bot2@tip-bot2/
- revert 补丁：https://lore.kernel.org/all/20261015082919.4344-1-kayracizmeci@gmail.com/
