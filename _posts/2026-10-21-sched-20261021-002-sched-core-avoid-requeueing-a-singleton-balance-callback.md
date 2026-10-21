---
id: sched-20261021-002
date: 2026-10-21
subject: 'sched/core: Avoid requeueing a singleton balance callback'
subsystem: sched
type: fix
status: under_review
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
- version: v1
  msgid: <20261020084400.845842-2-arighi@nvidia.com>
  date: 2026-10-20
  summary: 作为 3 补丁系列 1/3 首发，queue_balance_callback 增加链表头检查
  review_outcome: Tejun 要求重发给 Peter，并指出 head 检查只覆盖 singleton、尾条目仍漏
- version: v2
  msgid: <20261021070535.1256337-1-arighi@nvidia.com>
  date: 2026-10-21
  summary: 以 sched_ext/for-7.4-fixes 重发，补 rq->balance_callback == head 检查
  review_outcome: Tejun 与 Peter 均 Acked-by，待经 sched_ext 树路由
upstream_commit: null
fixes_commit: e2859566ffbc
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 长链表尾条目重复入队检测未覆盖（作者留作 follow-up）
  next_action: 由 Tejun 经 sched_ext/for-7.4-fixes 路由收取
contribution_opportunities:
- kind: new_patch
  description: 补充 queue_balance_callback 的长链表尾条目重复入队去重补丁
generated_at: '2026-10-22T01:30:00'
source_email_count: 6
related_articles: []
tags:
- sched_ext
- proxy_execution
title: 'sched/core: Avoid requeueing a singleton balance callback'
layout: article
---

## TL;DR
Andrea Righi 的修复：proxy execution 下 `__schedule()` 会对同一 donor 先 `SNT_REPICK` 再 `SNT_PICK`，两次都把 kick_sync balance callback 入队，而 `kick_sync_pending` 仍置位；当该 callback 是链表的唯一条目时，其 `next` 为 NULL，原有重复检查漏判，再次入队会把它链到自己，导致该 wait 被运行两次。修复在 `queue_balance_callback()` 增加「callback 是否已是链表头」检查。Tejun Heo 与 Peter Zijlstra 均已 Ack，待经 sched_ext 分支路由收取。

## 背景与问题
`queue_balance_callback()` 原有重复检查 `if (unlikely(head->next || rq->balance_callback == &balance_push_callback)) return;` 只覆盖两种情况：链表非空、或当前是 `balance_push_callback`。但当某个 callback 是链表唯一条目时，`head->next == NULL` 且 `rq->balance_callback == head`（不等于 `balance_push_callback`），检查漏判，重复入队会把 `head->next` 指向自身，形成自环，`do_balance_callbacks()` 遂把该 callback 执行两次。触发路径：proxy execution 下 `__schedule()` 对同一 donor 连续 `SNT_REPICK` 与 `SNT_PICK`，其间 kick_sync callback 被两次入队。Tejun 还指出：长链表的尾条目（`next == NULL` 且非链表头）同样可被再次入队（A→B→A 自环），但该尾条目场景不在本次修复范围内。

## 技术方案
单补丁（`kernel/sched/sched.h`，+2/-1）：在 `queue_balance_callback()` 的重复检查里加入 `rq->balance_callback == head`：

```c
- if (unlikely(head->next || rq->balance_callback == &balance_push_callback))
+ if (unlikely(head->next || rq->balance_callback == head ||
+              rq->balance_callback == &balance_push_callback))
```

由于 kick_sync callback 在 `SNT_REPICK` 与 `SNT_PICK` 之间没有其它东西入队，该 head 检查正好覆盖本例；长链表尾条目的重复入队仍可能，作者明确留作后续。

## 版本演进与当前进展
*current_version: v2（重发）*。

- v1（`<20261020084400.845842-2-arighi@nvidia.com>`，2026-10-20）：作为 3 补丁系列 `[PATCH 1/3] sched/core: Avoid requeueing a singleton balance callback` 首发（同系列 2/3 `sched_ext: Use irq_work for deferred actions with proxy execution`、3/3 `sched_ext: Remove the foreign CPU check from the kick_sync wait`）。Tejun 回复：请把 1/3 重发给 Peter、可加 Acked-by；并指出上面 head 检查只覆盖 singleton、尾条目仍漏。
- v2（`<20261021070535.1256337-1-arighi@nvidia.com>`，2026-10-21）：作者把 1/3 以 `[PATCH sched_ext/for-7.4-fixes]` 重发（因为触发 commit `e2859566ffbc` 只在 `sched_ext/for-7.4-fixes` 里），补上 head 检查。

## Maintainer 意见与讨论焦点
- Tejun Heo：最初要求「把 1/3 重发给 Peter」，并精准指出 tail-entry 重复入队问题；对重发版本给出 Acked-by。
- Peter Zijlstra：回复「Cute. OK, probably best if TJ routes it then? in which case: Acked-by」——即认可修复，且倾向由 Tejun 经 sched_ext 树路由（因触发 commit 在该树）。
- 作者 Andrea Righi 回应 Tejun：认同 tail-entry 案例，本修复保持针对已报告问题，tail 重复检测留作与 Peter 的后续单独补丁。

## 合入评估
*likelihood=high*。两位维护者（Tejun、Peter）均已 Acked-by，触发 commit 明确（`e2859566ffbc`）、带 `Fixes:`。*blocking_issues*：仅「长链表尾条目重复入队」未覆盖（作者留作 follow-up）。*next_action*：由 Tejun 经 `sched_ext/for-7.4-fixes` 路由收取。

## 效果评估
无 benchmark 数据。属正确性修复：消除 proxy execution 下 kick_sync wait 被重复运行（可导致冗余的 kick/唤醒路径执行两次）。

## 我可以参与的点
- `new_patch`：Tejun 指出的「长链表尾条目重复入队」检测目前未覆盖，可基于 `queue_balance_callback()` 的链表结构补充 tail-entry 去重补丁（Andrea 已表示会与 Peter 单独跟进，可作为其落地前的替代提案）。

## 参考链接
- v2 重发补丁：https://lore.kernel.org/all/20261021070535.1256337-1-arighi@nvidia.com/
- 原始 1/3：https://lore.kernel.org/all/20261020084400.845842-2-arighi@nvidia.com/
- Peter Acked-by：https://lore.kernel.org/all/20261021114555.GF2823843@noisy.programming.kicks-ass.net/
