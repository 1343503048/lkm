---
title: "sched/fair：重做/修复 task_h_load()"
date: 2026-09-02
tags: [sched/fair]
series: "sched fair rework task h load"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

`task_h_load()` 用于负载均衡时估算任务在层级 cgroup 下的「层级负载」，其计算在
cgroup 权重/层级变化后存在不一致或错误，影响 load balance 的迁移决策。本期对其做
重做/修复（作为某 4/4 或 7/7 系列的一部分，UID 72914 为 4/4）。

## 改动内容 / 核心补丁

- `[PATCH 4/4] sched/fair: Rework/fix task_h_load()`（UID 72914），配套 Re: 讨论
  （73218、73259、73677、73678、73685）。
- 修正层级负载的累加/缩放逻辑，使其在 cgroup 权重调整后给出一致结果。

## 状态与讨论

- 当前状态：**under_review**（作为多补丁系列的一部分推进）。
- 合入可能性 medium；影响 load balance 准确性，需维护者确认语义正确性。

## 关联

- 009 RFC v2 NUMA 细粒度均衡 + sched/cache 迁移辅助
- 015 sched：Remove sched_class::balance()
