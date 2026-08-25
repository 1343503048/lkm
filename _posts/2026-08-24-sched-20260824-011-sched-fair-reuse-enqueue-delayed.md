---
title: sched-20260824-011-sched-fair-reuse-enqueue-delayed
date: 2026-08-24
tags:
- sched/fair
- eevdf
series: reuse ENQUEUE_DELAYED avoid recalc curr
type: fix
severity: low
status: under_review
lore: ''
layout: article
---

## 概述

EEVDF 路径中，实体入队（enqueue）时涉及 `ENQUEUE_DELAYED` 标志与 `curr` 状态
的判定。本 2-patch 系列（UID 55148 1/2，UID 55133 2/2）建议：
1) 复用既有的 `ENQUEUE_DELAYED` 语义，减少特殊分支；
2) 在 `place_entity()` 与 `requeue_delayed_entity()` 中避免对 `curr` 状态做
   重复计算，降低冗余与潜在不一致。

## 改动内容 / 核心补丁

- (1/2) sched/fair: reuse the ENQUEUE_DELAYED ... ：统一 delayed 实体的入队处理。
- (2/2) sched/fair: avoid recalculating curr status in place_entity() and
  requeue_delayed_entity() ：去除重复的状态重算。

## 状态与讨论

- 当前状态：**under_review**。
- 与 009（Flatten the pick）及 EEVDF 单运行队列热点（85570f10a4c6）相关，属于
  fair 类内部清理与一致性改进。

## 关联

- 009 sched：Flatten the pick
- 006 sched/fair：v4.19 NULL deref
