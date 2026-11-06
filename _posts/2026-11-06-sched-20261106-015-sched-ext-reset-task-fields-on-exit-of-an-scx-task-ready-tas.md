---
id: sched-20261106-015
date: 2026-11-06
subject: 'sched_ext: Reset task fields on exit of an SCX_TASK_READY task'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261106142818.1475-1-rahadbhuiya2021@gmail.com>
lore_url: https://lore.kernel.org/all/20261106142818.1475-1-rahadbhuiya2021@gmail.com/
authors:
- Rahad Bhuiya
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261106142818.1475-1-rahadbhuiya2021@gmail.com>
  date: 2026-11-06
  summary: SCX_TASK_READY 退出路径补调 scx_reset_task_fields。
  review_outcome: 暂无评审。
upstream_commit: null
fixes_commit: a298fd5f4ee8
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Tejun Heo 审阅并应用
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Reset task fields on exit of an SCX_TASK_READY task'
layout: article
---

## TL;DR

Rahad Bhuiya 的 1 行修复（bpf-next，sched_ext）补上 `scx_reset_task_fields()` 的一个漏调用：任务以 `SCX_TASK_READY` 状态退出时（典型如「经 `ops.init_task()` 初始化、但从未在 ext_sched_class 下启用就退出」的 fork 任务，或 disabled 任务），`__scx_disable_and_exit_task()` 在状态机 switch 里直接 break 而不复位其 SCX 管理字段，违反「任务离开调度器控制后状态干净」的不变式。修复在该 case 里补调 `scx_reset_task_fields()`。`Fixes:` 指向引入该重构的 `a298fd5f4ee8`。

## 背景与问题

commit `a298fd5f4ee8`（"sched_ext: Fix use-after-free of a NONE rescuee leaving its sched while running"）把 SCX 管理字段（vtime、slice、reenqueue flags、watchdog `runnable_at`）的复位从 `scx_disable_task()` 抽到 `scx_reset_task_fields()`，以便在任务离开调度器控制的每条路径上都调用（含 `SCX_TASK_NONE`）。但 `__scx_disable_and_exit_task()` 里 `SCX_TASK_READY` 分支仍是空的 break——这类任务退出时字段不复位。

## 技术方案

在 `__scx_disable_and_exit_task()` 的 `case SCX_TASK_READY:` 里补上 `scx_reset_task_fields(task_rq(p), p)`，与其它退出路径一致。改动 `kernel/sched/ext/ext.c` 仅 +1 行。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。当日无评审。

## Maintainer 意见与讨论焦点

当日无回复。补丁是明确的不变式修复、`Fixes:` 齐全，无 NAK。

## 合入评估

*likelihood=high*。1 行、`Fixes` 清晰、属 for-7.x 类的对既有重构的补齐。*blocking_issues*：无显著阻塞（仅待 sched_ext 维护者 Tejun Heo 审阅）。*next_action*：等 Tejun Heo 审阅并应用。

## 效果评估

无性能数据。效果为不变式恢复——`SCX_TASK_READY` 退出路径的管理字段得到复位，避免残留状态污染后续。

## 我可以参与的点

当前阶段暂无明显参与空间（1 行修复待收取），可持续观察。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261106142818.1475-1-rahadbhuiya2021@gmail.com/
