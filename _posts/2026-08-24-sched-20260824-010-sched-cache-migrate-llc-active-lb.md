---
title: sched-20260824-010-sched-cache-migrate-llc-active-lb
date: 2026-08-24
tags:
- sched/cache
- load_balance
series: migrate_llc_task active load balance
type: fix
severity: medium
status: under_review
lore: ''
layout: article
---

## 概述

`migrate_llc_task` 提供了一种在 LLC 域内迁移任务的语义/提示。v3（Re: UID 54128）
讨论在 active load balance 路径中正确尊重该语义，避免把本应留在 LLC 内的任务
错误地迁移走，或不必要的跨域搬运。

## 改动内容 / 核心补丁

- 在 active load balance 的候选筛选与决策中纳入 `migrate_llc_task` 约束。
- 目标：在负载均衡收益与缓存局部性之间取得更优平衡。

## 状态与讨论

- 当前状态：**under_review（v3，回复形式）**。
- 持续性系列（往日已发 v1/v2/v3），本期为针对评审的修订/答复。

## 关联

- 009 sched：Flatten the pick
- 011 sched/fair：ENQUEUE_DELAYED / place_entity
