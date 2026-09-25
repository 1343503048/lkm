---
id: sched-20260925-003
date: 2026-09-25
subject: 'sched/fair: Remove dead code on enqueue_task_fair()'
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: <179033365207.2819794.11851486661940182495.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033365207.2819794.11851486661940182495.tip-bot2@tip-bot2/
upstream_commit: 819224e506bc7c2d61ec6a58ec6e876b505abce9
fixes_commit: null
merged_branch: tip/sched/core
current_version: v3
generated_at: '2026-09-26T01:15:00'
authors:
- Kayra Cizmeci
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: <20260911155449.1249726-1-kayracizmeci@gmail.com>
  date: 2026-09-11
  summary: 删除 enqueue_task_fair() 不可达的 cfs_rq->curr == se 分支（-13/+3）
  review_outcome: 无回帖；PeterZ 此前在 place_entity 线程给出等价 diff
- version: v3
  msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
  date: 2026-09-12
  summary: 补上版本号重发（作者自述漏标 v3），diff 与上次一致
  review_outcome: 09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260912-001
- sched-20260911-020
tags:
- cfs
title: 'sched/fair: Remove dead code on enqueue_task_fair()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/12/sched-20260912-001-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20260912-001</a> / <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-020-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20260911-020</a>。Kayra Cizmeci 的 enqueue_task_fair() 死代码清理已被 Peter Zijlstra 合入 tip/sched/core（commit 819224e506bc7c2d61ec6a58ec6e876b505abce9，09-25 12:45:57 +0200）。

## 背景与问题

`enqueue_task_fair()` 里有一段 `cfs_rq->curr == se` 的分支，实际是**不可达**的（enqueue 时被入队的实体不可能是当前正在运行的实体）。保留它既增加阅读负担，也带着一个只为该分支服务的 `bool curr` 变量。属于纯代码清理，无行为变更。

## 技术方案

删除依赖 `cfs_rq->curr == se` 的分支，以及为此引入的 `bool curr`；两种可能只剩一种后直接走另一分支。合入版本 diffstat：kernel/sched/fair.c 共 3 insertions(+), 13 deletions(-)。

## 版本演进与当前进展

- v1（无版本号投递，2026-09-11，`<20260911155449.1249726-1-kayracizmeci@gmail.com>`）：删除不可达分支（-13/+3）。
- v3（2026-09-12，`<20260911160253.1249960-1-kayracizmeci@gmail.com>`）：补上版本号重发（作者自述漏标 v3），diff 与上次一致。
- 09-25：Peter 合入 tip/sched/core（Commit-ID 819224e506bc7c2d61ec6a58ec6e876b505abce9）。

## Maintainer 意见与讨论焦点

本系列最早源自 Peter Zijlstra 在 place_entity 线程给出的等价 diff；作者据此独立成补丁。Ingo/Peter 侧以 committer 身份直接收取，本日无新讨论、无分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit 819224e506bc7c2d61ec6a58ec6e876b505abce9。纯死代码删除，无阻塞项。

## 效果评估

无运行时数据；属于可静态证明的清理（分支不可达）。暂无效果数据。

## 我可以参与的点

修复已合入，当前阶段暂无明显参与空间。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033365207.2819794.11851486661940182495.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/819224e506bc7c2d61ec6a58ec6e876b505abce9
- v3 补丁: https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
