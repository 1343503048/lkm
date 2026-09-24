# sched_ext: Derive SCX_RQ_IN_WAKEUP from the core enqueue flags

## TL;DR
Tejun Heo 提交 sched_ext/for-7.3-fixes 根因修复：`enqueue_task_scx()` 从合并后的 enqueue flags 派生 SCX_RQ_IN_WAKEUP，导致 `move_remote_task_to_local_dsq()` 在远端 rq 上置位该标志、却没有后续 `task_woken_scx()`，令 local reenqueue 请求被永久挂起、最终指向已释放的 per-cpu 区域（UAF）。修复改为只测试 core enqueue flags 的 wakeup 位。Andrea Righi 已给 Reviewed-by，且此补丁取代了他之前的"Unlink"方案。

## 背景与问题
`schedule_deferred_locked()` 在 SCX_RQ_IN_WAKEUP 置位时跳过调度 deferred action，依赖 wakeup enqueue 之后的 `task_woken_scx()` 来执行它。`enqueue_task_scx()` 从合并后的 enqueue flags（含为远端激活暂存的 flags）设置该标志，于是 `move_remote_task_to_local_dsq()` 在被移动任务曾唤醒时，会在目标 rq 上置位 SCX_RQ_IN_WAKEUP，但该激活路径后并无 `task_woken_scx()`。对一个忙碌目标 CPU 的 IMMED 插入会请求 local reenqueue，请求被链接却未被调度，一直挂到无关的唤醒/抢占才执行；若调度器被禁用前无人执行，请求就比调度器活得久、指向其已释放的 per-cpu 区域，下一次调度器从 `run_deferred()` 解引用造成 UAF。

## 技术方案
只测试 core enqueue flags 的 wakeup 位：只有 core 的 wakeup 路径之后才跟着 `task_woken_scx()`。改动集中在 `kernel/sched/ext/ext.c` 的 `enqueue_task_scx()`（6 增 1 删）。

## 版本演进与当前进展
v1（09-17，`<20260916215713.2701551-1-tj@kernel.org>`）刚发出，Andrea Righi 已给出 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Tejun Heo（作者）**：定位根因为 move_remote_task_to_local_dsq 的 enq_flags 暂存，自 57ccf5ccdc56 起这些 flags 决定 SCX_RQ_IN_WAKEUP。
- **Andrea Righi（Reported-by）**：认可"比我的修复更好"，给出 Reviewed-by。
- 无分歧；这是此前"Unlink pending"补丁的正确替代。

## 合入评估
*likelihood=high*。带 Fixes: 57ccf5ccdc56、Cc: stable v7.1+ 的根因修复，已有 Reviewed-by，无异议。*blocking_issues*：无。*next_action*：等待应用到 sched_ext/for-7.3-fixes。

## 效果评估
无性能数据；属 UAF/正确性修复。

## 我可以参与的点
- kind=testing：构造"忙碌远端 CPU 上 IMMED 插入 + 调度器禁用"场景，验证不再出现挂起请求指向已释放区域的 UAF。
- kind=review：核对 core enqueue flags 的 wakeup 位是否覆盖所有非 core-wakeup 的激活路径。

## 参考链接
- lore: https://lore.kernel.org/all/20260916215713.2701551-1-tj@kernel.org/

---
id: sched-20260917-011
date: '2026-09-17'
subject: 'sched_ext: Derive SCX_RQ_IN_WAKEUP from the core enqueue flags'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20260916215713.2701551-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20260916215713.2701551-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260916215713.2701551-1-tj@kernel.org>'
    date: '2026-09-17'
    summary: '只测试 core enqueue flags 的 wakeup 位来派生 SCX_RQ_IN_WAKEUP'
    review_outcome: 'Andrea Righi Reviewed-by'
upstream_commit: null
fixes_commit: '57ccf5ccdc56'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待应用到 sched_ext/for-7.3-fixes'
contribution_opportunities:
  - kind: testing
    description: '构造忙碌远端 CPU + IMMED 插入 + 调度器禁用场景验证 UAF 修复'
  - kind: review
    description: '核对 wakeup 位测试是否覆盖所有非 core-wakeup 激活路径'
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
  - sched-20260917-003
tags:
  - sched_ext
---