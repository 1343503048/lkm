---
id: sched-20261025-003
date: 2026-10-25
subject: 'sched/deadline: Fix this_bw on class change of a dying task'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261025124657.836229-1-nickolai@csail.mit.edu>
lore_url: https://lore.kernel.org/all/20261025124657.836229-1-nickolai@csail.mit.edu/
authors:
- Nickolai Zeldovich
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261025124657.836229-1-nickolai@csail.mit.edu>
  date: 2026-10-25
  summary: TASK_DEAD 的 this_bw 移除只在 dying 任务自己的 DEQUEUE_SLEEP dequeue 路径执行
  review_outcome: 无当日 review
upstream_commit: null
fixes_commit: 8fd27231c330
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 deadline 维护者 review
  next_action: 等 deadline 维护者 review 收取
contribution_opportunities:
- kind: testing
  description: 真实硬件/复杂 SCHED_FLAG_RECLAIM 负载上验证 GRUB 回收
- kind: review
  description: 核对 TASK_DEAD 移除在 DEQUEUE_SLEEP 与 switched_from_dl 路径的边界
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles: []
tags:
- deadline
title: 'sched/deadline: Fix this_bw on class change of a dying task'
layout: article
---

## TL;DR
Nickolai Zeldovich 发 v1 单补丁，修 SCHED_DEADLINE 任务在 `do_task_dead()` 置 `TASK_DEAD` 之后、`__schedule()` dequeue 之前被 `sched_setscheduler(2)` 移出类时 `this_bw` 被重复扣减的 bug：`this_bw` 直到重启都偏小，`__sub_rq_bw()` 报 underflow / `running_bw > this_bw` 的 WARN，且 SCHED_FLAG_RECLAIM 任务的 GRUB 回收被误算。补丁让 TASK_DEAD 的带宽扣减只在 dying 任务自己的 DEQUEUE_SLEEP dequeue 路径执行。

## 背景与问题
类变更用 `DEQUEUE_SAVE` 把仍排队的任务 dequeue，从 `running_bw` 和 `this_bw` 移除带宽；随后 `switched_from_dl()` → `task_non_contending()` 若 0-lag 时间已过，因任务已是 `TASK_DEAD` 又扣一次 `this_bw`——但这次扣减本意是给 dying 任务自己的 `DEQUEUE_SLEEP` dequeue 用的（那条路径此前什么也没扣）。双扣导致 `this_bw` 短账直到 reboot。`Fixes: 8fd27231c330`（"sched/deadline: Track the "total rq utilization" too"）。

## 技术方案
只在 dying 任务自己的 `DEQUEUE_SLEEP` dequeue 路径执行 TASK_DEAD 的带宽移除。

## 版本演进与当前进展
*current_version: v1*（`<20261025124657.836229-1-nickolai@csail.mit.edu>`）。当日新发，尚无 review。

## Maintainer 意见与讨论焦点
无维护者表态（当日）。

## 合入评估
*likelihood=high*。带明确 `Fixes:`、完整复现（QEMU x86_64 与 riscv64，50000 次迭代无 warning），属经典的调度带宽记账修复。*blocking_issues*：当日缓存未见 deadline 维护者 review。*next_action*：等 deadline 维护者 review 收取。

## 效果评估
QEMU x86_64（-smp 2）与 riscv64 复现：修复前约 1s 后命中 `task_non_contending`、`enqueue_dl_entity`、`switched_from_dl`、`dequeue_dl_entity` 四处 WARN；修复后 50000 次迭代无 warning。属正确性修复，无性能数据。

## 我可以参与的点
- *kind: testing*：在真实硬件/更复杂 SCHED_FLAG_RECLAIM 负载上验证 GRUB 回收不再误算。
- *kind: review*：核对 TASK_DEAD 移除在 DEQUEUE_SLEEP 路径与 switched_from_dl 路径的边界一致性。

## 参考链接
- patch: https://lore.kernel.org/all/20261025124657.836229-1-nickolai@csail.mit.edu/
