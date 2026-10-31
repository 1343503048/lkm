---
id: sched-20261030-009
date: 2026-10-30
subject: 'sched_ext: Fix stale pick when a wakeup resets the donor during dispatch'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261030142338.3453484-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261030142338.3453484-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 等待 sched_ext co-maintainer 的 Ack/Review
  next_action: 获 review 后合入 sched_ext/for-7.4-fixes
contribution_opportunities:
- kind: testing
  description: 在 proxy execution + sched_ext 下复跑 dispatch 期间被唤醒迁移场景，验证无 SCX_OPS_ENQ_LAST
    警告
- kind: review
  description: 核对 SCX_DSP_RETRY 重试路径是否会因反复 donor 变化引入活锁
generated_at: '2026-10-31T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- proxy_execution
title: 'sched_ext: Fix stale pick when a wakeup resets the donor during dispatch'
layout: article
---

## TL;DR
Tejun Heo 修 sched_ext 在 proxy execution 下的一个 stale pick 缺陷：`do_pick_task_scx()` 把 `rq->donor` 作为 `@prev` 传给 `dispatch_one()`，但 `dispatch_one()` 释放 rq lock 期间，别的 CPU 可能唤醒该 donor 并把它迁移走（`proxy_needs_return()` 会把它 dequeue、把 donor 重置回 `rq->curr`），导致 dispatch 返回的 verdict 描述的是**旧 donor**，最终本 CPU 去跑一个其实已排队到其它 rq 的任务。修法：`@prev` 不再是 donor 时 `SCX_DSP_RETRY` 重试 pick（`+10/-0`）。`Fixes: c6fe97c34a1a`，synthetic reproducer 验证。

## 背景与问题
proxy execution 下 `rq->donor` 与实际运行任务 `rq->diff`（donor != curr 的情况普遍存在）。`dispatch_one()` 为把其它 CPU 的任务移走会临时释放 rq lock，此时另一 CPU 唤醒 donor：proxy 迁移把它搬到本 CPU，`proxy_needs_return()` 将其 dequeue 并重置 donor 为 `rq->curr`，唤醒则可能把它 enqueue 到别的 CPU。于是 `dispatch_one()` 看到 `@prev` 仍 queued、返回 `SCX_DSP_PREV`，`do_pick_task_scx()` 返回 `@prev`，本 CPU 去跑一个排在别处 rq 的任务。其余 verdict 同样陈旧：`SCX_DSP_NONE` 会 pick idle、`put_prev_task_scx()` 把 `rq->curr` 停到本地 DSQ 却无人唤醒 CPU（或触发 `SCX_OPS_ENQ_LAST` 警告）；`SCX_DSP_LOCAL` 会在本不该抢占时抢占 `rq->curr`。`rq_modified_above()` 只在 `rq->curr` 属于 ext 之上的类时才捕获此次重置，dl_server pick 还会跳过该检查。

## 技术方案
在 `kernel/sched/ext/ext.c` 的 `dispatch_pick()` 里，`dispatch_one(rq, prev)` 返回后、`rq_repin_lock()` 之后，增加：

```c
if (unlikely(prev != rq->donor))
    return SCX_DSP_RETRY;
```

即「verdict 是为 `@prev` 算的，一旦 donor 变了就不适用，重启 pick」。重试以 `rq->curr` 作为 donor，而 `proxy_needs_return()` 对当前任务提前返回，donor 不会再变。作者说明不采用 `7a3a6bfbd62a`（"sched: Rework prev_balance() to avoid stale prev references"）那种「读 `rq->donor` 取代 `@prev`」的做法，因为此处 dispatch 从未评估过 `rq->curr`，而后者可能根本不是 sched_ext 任务。

## 版本演进与当前进展
*current_version: v1*（2026-10-30 发出）。首版，带 `Fixes:` 与 synthetic reproducer 验证结论，尚无 reviewer 回复。

## Maintainer 意见与讨论焦点
当日无独立 reviewer 回帖（作者即 sched_ext 维护者 Tejun Heo，发往 `sched_ext/for-7.4-fixes` 分支）。关键判断依据全部来自作者：mechanism 完整、有 `Fixes:` 指向 `c6fe97c34a1a`（prox 与 sched_ext 兼容性引入点）、并有 synthetic reproducer。

## 合入评估
*likelihood=high*。作者即子系统维护者、目标分支 `for-7.4-fixes`（-rc 修复窗口）、`Fixes:` 明确、有 reproducer 验证，合入阻力小。*blocking_issues*：暂无实质阻塞（盼 Andrea 等 co-maintainer 的 Ack/Review）。*next_action*：等 sched_ext co-maintainer review 后合入 `sched_ext/for-7.4-fixes`。

## 效果评估
作者标注「Verified with a synthetic reproducer」，未给出具体性能数字或复现脚本全文。

## 我可以参与的点
- **testing**：在启用 proxy execution + sched_ext 的场景复跑（dispatch 期间被唤醒迁移 donor），验证不再出现 `SCX_OPS_ENQ_LAST` 警告或跨 rq 误跑。
- **review**：核对 `SCX_DSP_RETRY` 重试路径是否会因反复 donor 变化引入活锁风险。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261030142338.3453484-1-tj@kernel.org/
