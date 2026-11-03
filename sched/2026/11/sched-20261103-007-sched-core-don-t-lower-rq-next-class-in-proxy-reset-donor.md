# sched/core: Don't lower rq->next_class in proxy_reset_donor()

## TL;DR

Tejun Heo 的 proxy execution urgent 修复：`proxy_reset_donor()` 无条件把 `rq->next_class` 设为 `rq->curr` 的类，会在「pick 掉锁后」窗口里把 RT wakeup 抬高过的 `next_class` 压低回 ext，导致 RT 任务要等下一次 schedule 才运行。修复改为只在 `curr->sched_class` 高于 `next_class` 时才抬高。`Fixes: c6fe97c34a1a`。

## 背景与问题

掉 rq 锁的 pick（`sched_balance_newidle()` 或 `do_pick_task_scx()`）会先把 `rq->next_class` 降到自己的类，重新拿锁后靠 `rq_modified_above()` 检测更高类 wakeup 并 restart。`proxy_reset_donor()` 无条件 `rq->next_class = rq->curr->sched_class`，可能在该窗口压低它。以 sched_ext 任务作 `rq->curr` 时的时序：1) fair 队列空、`sched_balance_newidle()` 掉锁且 `next_class` 停在 ext；2) RT wakeup 把 `next_class` 抬到 rt 并 `resched_curr()`；3) proxy exec 迁移来的 `rq->donor` 唤醒，`proxy_needs_return() → proxy_reset_donor()` 把 `next_class` 设回 ext；4) `rq_modified_above()` 看不到 fair 之上，sched_ext 返回任务、`__schedule()` 清 need_resched，RT 任务要等 CPU 下一次 schedule。需 sched_ext donor 才会触发；fair donor 时队列非空、newidle 不跑。sched_ext 场景自 `c6fe97c34a1a`（"sched: Allow enabling proxy exec with sched_ext"）起成为可能。

## 技术方案

`kernel/sched/core.c` 中 `proxy_reset_donor()` 把 `rq->next_class = rq->curr->sched_class` 改为条件式：`if (sched_class_above(rq->curr->sched_class, rq->next_class)) rq->next_class = rq->curr->sched_class;`。只抬不降——高于 `curr` 的 `next_class` 是任意更高类 wakeup 经 `wakeup_preempt()` 留下的（且 `->wakeup_preempt()` 自 `fa02b2868420` 起忽略他类 donor）；`proxy_reset_donor()` 里的 `resched_curr()` 让下次 pick 重设 `next_class`，保留的抬高让 `rq_modified_above()` 仍能捕获更高类 curr 的重置。

## 版本演进与当前进展

*current_version: v1（[PATCH sched/urgent]，2026-11-03 发出，msgid 20261102192907.2177529-1-tj@kernel.org）*。当日无回帖。

## Maintainer 意见与讨论焦点

无表态（作者即 sched_ext/proxy exec 维护者，刚发出）。

## 合入评估

*likelihood=high*。小修复（+6/−1）、有清晰 `Fixes:`、作者是 proxy exec 主要维护者，属 urgent 候选。

## 效果评估

作者说明是逻辑缺陷导致的调度延迟（RT 任务被延迟到下一次 schedule），未附量化 benchmark；`WARN_ON_ONCE(rq->donor == rq->curr)` 与 `resched_curr()` 交互的既有假设保持不变。

## 我可以参与的点

- testing：在开启 proxy exec + sched_ext 的负载上复现 RT wakeup 被延迟的场景并验证修复。
- review：核对 `sched_class_above()` 条件在 RT/DL donor 场景下是否覆盖所有合法状态。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261102192907.2177529-1-tj@kernel.org/

---
id: sched-20261103-007
date: 2026-11-03
subject: "sched/core: Don't lower rq->next_class in proxy_reset_donor()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261102192907.2177529-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261102192907.2177529-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261102192907.2177529-1-tj@kernel.org>"
    date: 2026-11-03
    summary: "proxy_reset_donor() 只在 curr 类更高时才抬高 next_class，不再无条件压低。"
    review_outcome: "刚发出，暂无 review。"
upstream_commit: null
fixes_commit: "c6fe97c34a1a"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 sched 维护者（Peter/Ingo）收取。"
contribution_opportunities:
  - kind: testing
    description: "proxy exec + sched_ext 负载上复现 RT wakeup 延迟并验证修复。"
  - kind: review
    description: "核对 sched_class_above 条件覆盖 RT/DL donor 全状态。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [proxy_execution]
---