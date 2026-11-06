---
id: sched-20261106-026
date: 2026-11-06
subject: 'sched/deadline: Fix this_bw on class change of a dying task'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <179395864120.1009794.11212049218049367777.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179395864120.1009794.11212049218049367777.tip-bot2@tip-bot2/
authors:
- Nickolai Zeldovich
maintainers_involved:
- Ingo Molnar
- Peter Zijlstra
- Juri Lelli
current_version: v1
patch_series:
- version: v1
  msgid: <20261025124657.836229-1-nickolai@csail.mit.edu>
  date: 2026-10-25
  summary: TASK_DEAD this_bw 扣减仅限 dl_task，避免 class 切换重复扣。
  review_outcome: Juri Acked-by + Tested-by；11-06 合入 tip/sched/urgent。
upstream_commit: 0c93e25ef11a9dee43f6076bd1f09771dc2b167e
fixes_commit: 8fd27231c330
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 进入主线
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261027-006
tags:
- deadline
title: 'sched/deadline: Fix this_bw on class change of a dying task'
layout: article
---

## TL;DR

Nickolai Zeldovich 的修复今日合入 tip/sched/urgent（commit `0c93e25ef11a9dee43f6076bd1f09771dc2b167e`）：SCHED_DEADLINE 任务在 `do_task_dead()` 置 `TASK_DEAD` 之后、`__schedule()` dequeue 之前被 `sched_setscheduler(2)` 移出类时，`this_bw` 被重复扣减——此后 `this_bw` 短账直到 reboot，`__sub_rq_bw()` 告警 underflow 或 `running_bw > this_bw`，该 CPU 上 SCHED_FLAG_RECLAIM 任务的 GRUB 回收被误算。修复让 TASK_DEAD 带宽扣减只在 dying 任务自己的 `DEQUEUE_SLEEP` dequeue 路径执行。此前已获 Juri Lelli 的 Acked-by + Tested-by。

## 背景与问题

`task_non_contending()` 里对 `TASK_DEAD` 任务的 `sub_rq_bw()`，其本意是处理 dying 任务自己的 `DEQUEUE_SLEEP` dequeue（那之前没有任何删除）。但 class-change dequeue 会先以 `DEQUEUE_SAVE` 把仍入队的任务从 `running_bw`/`this_bw` 移除，随后 `switched_from_dl()` 再调 `task_non_contending()`——0-lag 时间已过时再次 `sub_rq_bw()`，`this_bw` 被扣两次。

## 技术方案

`task_non_contending()` 里把条件从 `if (READ_ONCE(p->__state) == TASK_DEAD)` 改为 `if (dl_task && READ_ONCE(p->__state) == TASK_DEAD)`——只有「仍是 deadline 任务」的 dying 任务才走这条 TASK_DEAD 扣减路径（即其自身的 DEQUEUE_SLEEP），迁出类的任务不再重复扣。改动 `kernel/sched/deadline.c` 仅 1 行。

## 版本演进与当前进展

*current_version: v1（2026-10-25 发出）*。10 月 Juri Lelli 复现并给 Tested-by + Acked-by。今日合入 tip/sched/urgent。

## Maintainer 意见与讨论焦点

Juri Lelli（SCHED_DEADLINE 维护者）Acked-by + Tested-by；Peter/Ingo 连带 Signed-off-by。无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，commit `0c93e25ef11a9dee43f6076bd1f09771dc2b167e`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线。

## 效果评估

提交说明：QEMU 上 x86_64 与 riscv64 循环把 exiting deadline 任务迁到 SCHED_OTHER，修前 `this_bw` 短账触发告警，修后无告警。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/0c93e25ef11a9dee43f6076bd1f09771dc2b167e
- 原补丁 lore: https://patch.msgid.link/20261025124657.836229-1-nickolai@csail.mit.edu
