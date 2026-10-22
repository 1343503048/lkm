---
id: sched-20261022-015
date: 2026-10-22
subject: 'sched/core: Avoid requeueing a singleton balance callback'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261021070535.1256337-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261021070535.1256337-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261021070535.1256337-1-arighi@nvidia.com>
  date: 2026-10-21
  summary: queue_balance_callback() 加 head 检查避免 singleton 重复入队
  review_outcome: Tejun Heo + Peter Zijlstra Ack；应用到 sched_ext/for-7.4-fixes
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 sched_ext/for-7.4-fixes，等待随修复流进主线
contribution_opportunities: []
generated_at: '2026-10-23T01:20:00'
source_email_count: 1
related_articles:
- sched-20261021-002
tags:
- sched_ext
- proxy_execution
title: 'sched/core: Avoid requeueing a singleton balance callback'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-002-sched-core-avoid-requeueing-a-singleton-balance-callback.html">sched-20261021-002</a>：Andrea Righi 的修复：proxy execution 下 `__schedule()` 会对同一 donor 先 `SNT_REPICK` 再 `SNT_PICK`，两次都把 kick_sync balance callback 入队，而 `kick_sync_pending` 仍置位；当该 callback 是链表唯一条目时其 `next` 为 NULL，原有重复检查漏判，再次入队会把它链到自己，导致该 wait 被运行两次。修复在 `queue_balance_callback()` 增加「callback 是否已是链表头」检查。Tejun Heo 与 Peter Zijlstra 均已 Ack，待经 sched_ext 分支路由收取。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-015-sched-core-avoid-requeueing-a-singleton-balance-callback.html">sched-20261022-015</a>（今天）：Tejun Heo 将其应用到 sched_ext/for-7.4-fixes，并补上 `Acked-by: Peter Zijlstra (Intel)` 标签。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-002-sched-core-avoid-requeueing-a-singleton-balance-callback.html">sched-20261021-002</a>）`queue_balance_callback()` 原有重复检查只覆盖「链表非空」与「当前是 `balance_push_callback`」两种情况；当某 callback 是链表唯一条目（`head->next == NULL` 且 `rq->balance_callback == head`）时漏判，重复入队把 `head->next` 指向自身形成自环，`do_balance_callbacks()` 于是执行两次。触发路径：proxy execution 下 `__schedule()` 对同一 donor 连续 `SNT_REPICK` 与 `SNT_PICK`。

## 技术方案
（承接前版）单补丁（`kernel/sched/sched.h`，+2/-1）：在 `queue_balance_callback()` 的重复检查里加入 `rq->balance_callback == head`。长链表尾条目的重复入队仍可能，作者留作后续。今日仅由 Tejun 收取并补 Acked-by。

## 版本演进与当前进展
*current_version: v2*（`<20261021070535.1256337-1-arighi@nvidia.com>`）。当日被应用到 sched_ext/for-7.4-fixes。

## Maintainer 意见与讨论焦点
Peter Zijlstra（Intel）此前已 Ack；Tejun Heo 今日收取并补 Acked-by 标签，无额外异议。

## 合入评估
*likelihood=merged*。已进入 sched_ext/for-7.4-fixes（`merged_branch=sched_ext/for-7.4-fixes`），待随 7.4 修复流汇入主线。

## 效果评估
修复 balance callback 被重复执行的问题（proxy execution 场景）；无量化性能数据。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261021070535.1256337-1-arighi@nvidia.com/
- Tejun 今日回帖：https://lore.kernel.org/all/7350d12ddf2d800823dfc1366e91ff2d@kernel.org/
