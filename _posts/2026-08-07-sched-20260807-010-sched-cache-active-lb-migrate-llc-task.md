---
subject: 'sched/cache: 在 active load balance 中落实 migrate_llc_task 语义'
date: 2026-08-07
series: sched-cache-active-lb-migrate-llc
version: v1
status: in-review
tags:
- sched/cache
- load_balance
- affinity
related_articles: []
submitter: 社区
emails:
- uid: 26556
  subject: 'Re: [PATCH] sched/cache: honor migrate_llc_task semantics in active load
    balance'
- uid: 25059
  subject: '[PATCH] sched/cache: honor migrate_llc_task semantics in active load balance'
- uid: 26191
  subject: 'Re: [PATCH] sched/cache: honor migrate_llc_task semantics in active load
    balance'
title: 'sched/cache: 在 active load balance 中落实 migrate_llc_task 语义'
layout: article
---

## 概述

围绕 `migrate_llc_task` 迁移语义在 active load balance（ALB）路径中的落实，Chen Yu C 与 Tim Chen 等展开讨论，目标是为 per-task 的 LLC 内迁移策略提供细粒度控制。

## 讨论要点

- Chen Yu C 指出该方案对 per-task 基础迁移策略提供了细粒度控制，但有细节：若在 `can_migrate_task()` 中覆盖 ALB 的 `migration_type`（默认 `migrate_load`），则被延迟的任务（sched_delayed）可能因 `migration_type != migrate_load` 而不在 ALB 中迁移。建议通过 `env->flags` 传递 `migrate_llc_task` 信息（新增 `LBF_ACTIVE_LB_LLC` 标志）。
- Tim Chen 建议更简洁地新增 `migrate_llc_task_alb` 迁移类型，并相应修改 `can_migrate_task()` 的拒绝条件，使其同时允许 `migrate_load` 与 `migrate_llc_task_alb`。
- 仍需一条通道将 `migrate_llc_task`/`migrate_llc_task_alb` 带入 ALB。

## 状态

处于设计讨论阶段，尚未形成定稿实现。

## 参考链接

- 邮件：uid 26556 / 25059 / 26191
