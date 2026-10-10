---
id: sched-20261010-009
date: '2026-10-10'
subject: 'sched_ext: Don''t leave balance callbacks queued across a pick retry'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010095208.276806-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261010095208.276806-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261010095208.276806-1-arighi@nvidia.com>
  date: '2026-10-10'
  summary: 仅 pick 最终确定时排队 balance callback，其余 defer 到 irq_work
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: 4c95380701f5
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: high
  blocking_issues:
  - Tejun 的收取未发生
  next_action: 等 Tejun applied 到 sched_ext/for-7.3-fixes
contribution_opportunities:
- kind: testing
  description: 用 vng + scx_qmap -I + stress-ng --sched fifo 复现并验证不再 WARN
- kind: review
  description: 复核 dl_server NULL 与 RETRY_TASK 两条路径的 defer 覆盖
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Don''t leave balance callbacks queued across a pick retry'
layout: article
---

## TL;DR
Andrea Righi 发往 `sched_ext/for-7.3-fixes` 的新修复：dispatch 路径可能在 `pick_task_scx()` 尚未结束时（`RETRY_TASK` 或 dl_server 返回 NULL 后继续挑低优先级类）就排好 `rq->scx.deferred_bal_cb`，而 balance callback 本必须在下一次释放 rq 锁前被消费——期间 rq 锁可被再次释放（`prev_balance()` 的 `balance_rt()`/`pull_rt_task()`），任何在本窗口拿锁的 CPU 都会撞上 pending balance callback 并触发 `rq_pin_lock()` 的 WARNING。修复改为只在 pick 确定时才排队 balance callback，其余 defer 到 irq_work。带 `Fixes: 4c95380701f5`、`Cc: stable v6.19+`。当日新发，无回帖。

## 背景与问题
dispatch 路径可请求「下次从 balance callback 跑 deferred work」，而 `pick_task_scx()` 在 dispatch 之后立即排 `rq->scx.deferred_bal_cb`。但 balance callback 必须在 rq 锁释放前被消费，`pick_task_scx()` 未必是 pick 的终点：① 在 dispatch 持锁释放期间有更高优先级类任务被 enqueue 时返回 `RETRY_TASK`；② `dl_server` pick 可能返回 NULL、随后挑更低优先级类。两种情况下 callback 仍挂在队列、核心继续挑任务，rq 锁可被再次释放。作者给出复现（RT 任务为 prev 时）：`__pick_next_task → pick_task_scx → dispatch_pick → maybe_queue_balance_callback` 之后 `RETRY_TASK`，随后 `prev_balance → balance_rt → pull_rt_task → double_lock_balance` 释放 rq 锁——任何本窗口内拿到 rq 锁的 CPU 都在 `rq_pin_lock()` 触发 WARNING。可复现命令：`scx_qmap -I` 配合频繁睡眠的 SCHED_FIFO 负载（stress-ng）。

## 技术方案
单补丁（`kernel/sched/ext/ext.c` +51/-23）：只在 pick **最终确定**时才排 balance callback；否则把 deferred 工作改走 irq_work 路径（不依赖当前 rq 锁段），并让 kick-sync 等待挂到下一次 pick。从 `dispatch_pick()` 移除 `maybe_queue_balance_callback()` 与同步等待的排队逻辑。

## 版本演进与当前进展
*current_version: v1*（单枚，`<20261010095208.276806-1-arighi@nvidia.com>`）。当日新发到 `sched_ext/for-7.3-fixes`，无回帖。

## Maintainer 意见与讨论焦点
当日无回帖。作者即 sched_ext 维护者、直发 for-7.3-fixes，带有真实 WARNING 栈与 `stress-ng` 复现命令。潜在评审点（无人提出）：defer 到 irq_work 后「kick-sync 等待挂到下一次 pick」的时序是否完整。

## 合入评估
*likelihood=high*（预期）。维护者直发目标 fixes 分支、带 `Fixes:`/`Cc: stable v6.19+`、有清晰复现；按 sched_ext 惯例待 Tejun 逐补丁收取。*blocking_issues*：Tejun 的收取未发生。*next_action*：等 Tejun applied 到 sched_ext/for-7.3-fixes。

## 效果评估
作者给出复现：16 CPU 虚拟机上 `scx_qmap -I` + 频繁睡眠的 SCHED_FIFO 负载，触发 `rq_pin_lock()` 的 WARNING（`WARNING: kernel/sched/sched.h:1919 at rq_lock`，CPU#10 stress-ng-sleep）。修复效果为消除该 WARNING，无性能数据。

## 我可以参与的点
- 用文中给定的 `vng` + `scx_qmap -I` + `stress-ng --sched fifo` 命令复现并验证修复后不再 WARN；
- 复核 defer 到 irq_work 分支在 dl_server NULL / RETRY_TASK 两条路径上的覆盖。

## 参考链接
- patch: https://lore.kernel.org/all/20261010095208.276806-1-arighi@nvidia.com/
