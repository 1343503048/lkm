---
id: sched-20261118-008
date: '2026-11-18'
subject: 'sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261118065921.98260-1-fushuai.wang@linux.dev>
lore_url: https://lore.kernel.org/all/20261118065921.98260-1-fushuai.wang@linux.dev/
authors:
- Fushuai Wang
maintainers_involved:
- Shrikanth Hegde
current_version: v2
patch_series:
- version: v1
  msgid: <20261109083130.1679-1-fushuai.wang@linux.dev>
  date: '2026-11-09'
  summary: 在 stopper 里重检 is_migration_disabled 再 __migrate_task
  review_outcome: Shrikanth 追问复现方式
- version: v2
  msgid: <20261118065921.98260-1-fushuai.wang@linux.dev>
  date: '2026-11-18'
  summary: 补全竞态时序与 WARNING 栈，重检 is_migration_disabled
  review_outcome: Shrikanth Reviewed-by
upstream_commit: null
fixes_commit: 74699f56ebcf
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 无 Peter/Ingo 评审
  next_action: 等 sched maintainer 收取
contribution_opportunities:
- kind: testing
  description: 复现该 WARNING 并验证 v2 后消失
- kind: review
  description: 确认重检覆盖所有 migrate_disable 空窗
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261109-011
tags:
- cfs
- preempt
title: 'sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-011-sched-core-fix-a-toctou-bug-in-sched-non-preferred-cpu-pu.html">sched-20261109-011</a>：Fushuai Wang 发 v1 修 `sched_non_preferred_cpu_push_stop()` 的 TOCTOU 竞态——`sched_push_current_non_preferred_cpu()` 在 irq 上下文先查 `is_migration_disabled()` 再排队 stopper，任务可能在 stopper 执行前进入 `migrate_disable()`；v1 在 stopper 里重检后再 `__migrate_task()`。Shrikanth 追问复现方式。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-008-sched-core-fix-a-toctou-bug-in-sched-non-preferred-cpu-pu.html">sched-20261118-008</a>（今天）：**v2 发出**，补全详细竞态时序（`migrate_disable()` 在 `preempt_disable()` 段内设 `p->migration_disabled`，irq 可落在两者之间）+ 完整 WARNING 栈；Shrikanth 给 Reviewed-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-011-sched-core-fix-a-toctou-bug-in-sched-non-preferred-cpu-pu.html">sched-20261109-011</a>）`migrate_disable()` 在 `preempt_disable()` 段内设置 `p->migration_disabled = 1`；一个 irq 可在 `preempt_disable()` 之后、`migration_disabled = 1` 之前命中。irq 返回后任务因抢占关闭无法被 stopper 抢占，会先把 `migration_disabled = 1` 设完再轮到 stopper 运行——即排队 stopper 时读到的是「尚未 migrate-disabled」的旧值，而 stopper 执行时任务已是 migrate-disabled，若仍 `__migrate_task()` 就触发 `set_task_cpu` 的 WARNING。

## 技术方案

v2 在 v1 基础上把竞态时序写清楚，并给出完整 WARNING 栈：

```
WARNING: kernel/sched/core.c:3432 at set_task_cpu+0x1b8/0xdf0, CPU#21: migration/21/152
Stopper: sched_non_preferred_cpu_push_stop+0x0/0xb10 <- sched_push_current_non_preferred_cpu+0x6a6/0x9a0
move_queued_task → sched_non_preferred_cpu_push_stop+0x7b7/0xb10 → cpu_stopper_thread
```

修法：在 `sched_non_preferred_cpu_push_stop()` 里、`__migrate_task()` 之前重新检查 `is_migration_disabled()`，使 migrate-disabled 任务不再进入迁移路径。

## 版本演进与当前进展

*current_version: v2（2026-11-18 发出，`<20261118065921.98260-1-fushuai.wang@linux.dev>`）*。v2 补全竞态时序与 WARNING 栈（v1 仅一句复现说明）。Shrikanth 当日给 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Shrikanth Hegde**：`Reviewed-by`（「Thanks for the fix」），此前 v1 的复现追问已在 v2 得到回答。
- 尚无 Peter/Ingo 表态。

## 合入评估

*likelihood=medium*。已获 Shrikanth 的 Reviewed-by，修法符合既有模式（stopper 内重检），但 sched maintainer 尚未收取。*blocking_issues*：① 无 Peter/Ingo 评审。*next_action*：等 sched maintainer 收取。

## 效果评估

作者给出完整 WARNING 栈（`set_task_cpu+0x1b8/0xdf0`，`migration/21` stopper），未给修复后验证数据或触发频率；属并发正确性修复。

## 我可以参与的点

- **review**：确认 v2 的重检在 stopper 上下文的锁/时序下是否覆盖所有 migrate_disable 空窗。
- **testing**：在开启 non-preferred CPU push 的平台复现该 WARNING 并验证 v2 后消失。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261118065921.98260-1-fushuai.wang@linux.dev/
- Shrikanth 的 Reviewed-by: https://lore.kernel.org/all/512ba302-9dcd-4ce4-9331-a6e545c36a8a@linux.ibm.com/
