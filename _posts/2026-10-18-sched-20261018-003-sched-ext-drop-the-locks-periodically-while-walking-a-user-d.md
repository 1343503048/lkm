---
id: sched-20261018-003
date: 2026-10-18
subject: 'sched_ext: Drop the locks periodically while walking a user DSQ for re-enqueue'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261017235840.1446655-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261017235840.1446655-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261017235840.1446655-1-tj@kernel.org>
  date: 2026-10-17
  summary: 按访问数而非重入队数计数，每 SCX_TASK_ITER_BATCH 访问掉双锁，避免长未标记任务段在双锁+IRQs off 下被遍历
  review_outcome: Andrea Righi Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已应用 sched_ext/for-7.4，随 7.4 合入窗口进主线
contribution_opportunities:
- kind: testing
  description: 在含大量未标记任务的用户 DSQ 上压测 SCX_REENQ_MARKED 过滤路径的掉锁与 cursor 保位
generated_at: '2026-10-19T09:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Drop the locks periodically while walking a user DSQ for re-enqueue'
layout: article
---

## TL;DR

Tejun Heo 发往 `sched_ext/for-7.4` 的单补丁：`reenq_user()` 此前每个 re-enqueue 掉一次 dsq->lock、每 `SCX_TASK_ITER_BATCH` 个 re-enqueue 掉一次 rq 锁，但被 `SCX_REENQ_MARKED` 过滤的 walk 会跳过未标记任务而不掉锁——一整段未标记任务可在一次持锁（双锁 + IRQs off）内被遍历完。补丁改为按「访问数」而非「重入队数」计数掉锁。Andrea Righi `Reviewed-by`，Tejun 已应用。

## 背景与问题

`reenq_user()` 在每次 re-enqueue 周围掉 dsq->lock、每 `SCX_TASK_ITER_BATCH` 次 re-enqueue 掉一次 rq 锁。但 `SCX_REENQ_MARKED` 过滤的 walk（本日 `scx_bpf_dsq_reenq_task()` 系列的产物）会跳过未标记任务而不掉任何锁，于是很长一段未标记任务在「同时持有两个锁、IRQs 关闭」的状态下被遍历——这是 Andrea Righi 在 review `scx_bpf_dsq_reenq_task()` 2/3 时点出的非阻塞问题（IRQs off 长锁遍历全体）。

## 技术方案

单补丁（`kernel/sched/ext/ext.c`，+16/−8）：把计数从「已重入队数」（`nr_enqueued`）改为「已访问数」（`nr_visited`），每 `SCX_TASK_ITER_BATCH` 次访问就同时掉 dsq->lock 与 rq 锁（cursor 保位）。未过滤的 walk 掉锁频率与之前一致。`Suggested-by: Andrea Righi`。

## 版本演进与当前进展

*current_version: v1*。单补丁当日新发，随即获评并应用。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者）：「Looks good!」并给 `Reviewed-by`。无分歧。

## 合入评估

*likelihood=merged*。Tejun 已应用到 `sched_ext/for-7.4`，并追加 `Reviewed-by: Andrea Righi` 标签。*blocking_issues*：无。*next_action*：随 for-7.4 进 7.4 合入窗口。

## 效果评估

无 benchmark 数字；属锁持有时长/IRQs 关闭时长的健壮性改进，避免长 DSQ 遍历在双锁 + IRQs off 下跑完。效果为定性的「掉锁频率恢复正常」。

## 我可以参与的点

- `testing`：在含大量未标记任务的用户 DSQ 上压测 re-enqueue walk（尤其 `SCX_REENQ_MARKED` 过滤路径），观察掉锁后的延迟中断恢复与 cursor 保位正确性。
- `extend`：若观察到 cursor 保位在并发迭代下的边界问题，可基于此发后续补丁。

## 参考链接

- 补丁：https://lore.kernel.org/all/20261017235840.1446655-1-tj@kernel.org/
- Andrea Righi Reviewed-by：https://lore.kernel.org/all/atRiJSZfbaRunnkL@gpd4/
- Tejun 应用确认：https://lore.kernel.org/all/f142e8fb9d61dff037548268fab78d5c@kernel.org/
