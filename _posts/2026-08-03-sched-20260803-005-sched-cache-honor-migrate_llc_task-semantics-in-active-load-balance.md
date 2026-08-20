---
id: sched-20260803-005
date: 2026-08-03
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Lu Wang
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Dietmar Eggemann
current_version: v4
patch_series:
- version: v4
  msgid: <unknown>
  date: 2026-08-03
  summary: active load balance 用 can_migrate_task() 检查，但后者允许 !migration_disabled 的任务迁移，而
    active LB 应尊重 migrate_llc_task 的「仅在任务本地 LLC 内迁移」语义。改为引入 can_migrate_llc_task()
    显式尊重该标志，并在 task_can_migrate() 内复用，消除与 can_migrate_task() 的语义重复。
  review_outcome: Peter Zijlstra 指出『要么避免重复，要么避免歧义』，要求把 can_migrate_llc_task() 放进 task_can_migrate()
    由 active LB 复用。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需按 PeterZ 意见把 can_migrate_llc_task() 统一进 task_can_migrate()，消除 can_migrate_task()
    与 active LB 两条路径的语义分歧
  next_action: 等待作者按 PeterZ 反馈重排 helper 归属后发 v5；属清理+修正，合入阻力小。
contribution_opportunities:
- kind: review
  description: active load balance 路径的 migrate_llc_task 语义边界（仅本地 LLC 内迁移）是否应与 can_migrate_task()
    完全一致，可审阅 v5 的 helper 合并是否引入新的行为偏差。
generated_at: '2026-08-04T00:20:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
- affinity
title: sched cache honor migrate_llc_task semantics in active load balance
layout: article
---

# sched/cache: active load balance 尊重 migrate_llc_task 语义


## TL;DR
`sched/cache` 修正 active load balance 未尊重 `migrate_llc_task` 的「仅本地 LLC 内迁移」语义。Peter Zijlstra 要求消除与 `can_migrate_task()` 的语义重复。待 v5 收敛，合入可能性高。

## 背景与问题
`migrate_llc_task` 是用户/sysctl 控制的标志，要求「任务仅在自身本地 LLC 内迁移」。但 active load balance（busy CPU 被强制拉走任务）走的是 `can_migrate_task()`，该函数只检查 `!migration_disabled`，会忽略 `migrate_llc_task` 的约束，导致任务可能被迁移出本应锁定的本地 LLC 域，违背用户意图并影响缓存局部性。

## 技术方案
引入 `can_migrate_llc_task()`，把「尊重 `migrate_llc_task` 仅在本地 LLC 内迁移」的语义独立成 helper；active LB 改用它做检查。v4 中 Peter Zijlstra 进一步要求：把 `can_migrate_llc_task()` 放进 `task_can_migrate()`，由 active LB 复用，从而消除 `can_migrate_task()` 与 active LB 两条迁移检查路径的语义分歧（要么避免重复，要么避免歧义）。

## 版本演进与当前进展
当前 v4（2026-08-03）。此前版本（v3 及更早）已迭代过 set_cpus_allowed 路径与 active LB 的一致性。Peter Zijlstra 在 16654 直接给出代码级修改建议。

## Maintainer 意见与讨论焦点
Peter Zijlstra（核心 maintainer）给出明确重构意见：把 LLC 语义 helper 合入 `task_can_migrate()`，避免两条路径语义分叉。角度属实现整洁性+正确性，非方向反对。

## 合入评估
合入可能性 high。是正确性+重构修正，等作者按反馈发 v5 即可。无架构级分歧。

## 效果评估
邮件未提供 benchmark；属缓存局部性与策略正确性修复，效果以「尊重 migrate_llc_task 约束」衡量。无量化数据。

## 我可以参与的点
- v5 发布后审阅 `can_migrate_llc_task()` 合并进 `task_can_migrate()` 是否改变了其他调用点的迁移行为（如 nohz/stop 路径），回帖确认无回归。

## 参考链接
- lore thread: 未获取到
