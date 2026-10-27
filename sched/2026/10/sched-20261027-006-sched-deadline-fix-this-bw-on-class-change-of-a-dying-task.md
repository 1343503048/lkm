# sched/deadline: Fix this_bw on class change of a dying task

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-003（v1）：Nickolai Zeldovich 修 SCHED_DEADLINE 任务在 `do_task_dead()` 置 `TASK_DEAD` 后、`__schedule()` dequeue 前被 `sched_setscheduler(2)` 移出类时 `this_bw` 被重复扣减的 bug（`this_bw` 短账直到 reboot、GRUB 回收误算）。补丁让 TASK_DEAD 带宽扣减只在 dying 任务自己的 DEQUEUE_SLEEP dequeue 路径执行。
- sched-20261027-006（今天）：deadline 维护者 Juri Lelli 复现并给出 `Tested-by` + `Acked-by`，补丁实质 ready。

## 背景与问题
（承接 20261025-003）类变更用 `DEQUEUE_SAVE` 把仍排队的任务 dequeue、从 `running_bw`/`this_bw` 移除带宽；随后 `switched_from_dl()` → `task_non_contending()` 若 0-lag 已过，因任务已 `TASK_DEAD` 又扣一次 `this_bw`——但这次扣减本意是给 dying 任务自己的 `DEQUEUE_SLEEP` dequeue 用的。双扣导致 `this_bw` 短账直到 reboot。`Fixes: 8fd27231c330`。

## 技术方案
（承接 v1）只在 dying 任务自己的 `DEQUEUE_SLEEP` dequeue 路径执行 TASK_DEAD 的带宽移除。

## 版本演进与当前进展
*current_version: v1*。今日 Juri Lelli 把复现器收编进其 `sched-deadline-tests` 仓库并回帖 `Tested-by` + `Acked-by`；Nickolai 表示「fine plan」。

## Maintainer 意见与讨论焦点
Juri Lelli（deadline 维护者）明确 `Tested-by` + `Acked-by`，无分歧。

## 合入评估
*likelihood=high*。带 `Fixes:`、有完整复现、deadline 维护者已 Acked，基本等收取。*blocking_issues*：无硬性阻断。*next_action*：等维护者收入 tip/sched/urgent 或调度修复分支。

## 效果评估
QEMU x86_64（-smp 2）与 riscv64 复现：修复前 ~1s 内命中四处 WARN；修复后 50000 次迭代无 warning（承接 v1 数据）。

## 我可以参与的点
- *kind: testing*：在更复杂 SCHED_FLAG_RECLAIM 负载下验证 GRUB 回收不再误算。

## 参考链接
- 线程: https://lore.kernel.org/all/20261025124657.836229-1-nickolai@csail.mit.edu/

---
id: sched-20261027-006
date: 2026-10-27
subject: 'sched/deadline: Fix this_bw on class change of a dying task'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261025124657.836229-1-nickolai@csail.mit.edu>'
lore_url: 'https://lore.kernel.org/all/20261025124657.836229-1-nickolai@csail.mit.edu/'
authors:
  - 'Nickolai Zeldovich'
maintainers_involved:
  - 'Juri Lelli'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261025124657.836229-1-nickolai@csail.mit.edu>'
    date: 2026-10-25
    summary: 'TASK_DEAD 的 this_bw 移除只在 dying 任务自己的 DEQUEUE_SLEEP dequeue 路径执行'
    review_outcome: 'Juri Lelli Tested-by + Acked-by'
upstream_commit: null
fixes_commit: '8fd27231c330'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等维护者收入调度修复分支'
contribution_opportunities:
  - kind: testing
    description: '更复杂 SCHED_FLAG_RECLAIM 负载下验证 GRUB 回收'
generated_at: '2026-10-28T09:00:00'
source_email_count: 2
related_articles:
  - sched-20261025-003
tags:
  - deadline
---