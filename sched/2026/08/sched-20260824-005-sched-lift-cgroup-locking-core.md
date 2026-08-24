---
title: "sched：将 cgroup 更新锁上提到 core"
date: 2026-08-24
tags: [cgroup, sched/core, sched_ext]
series: "lift cgroup update locking to core"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

cgroup 调度相关的更新锁原本分散在 fair/rt 等具体类中，导致 sched_ext 等路径
难以统一获取一致的保护。v3（UID 54466）将 cgroup 更新锁上提到调度 core，统一
加锁语义，使各调度类与 sched_ext 都能复用同一把锁。

## 改动内容 / 核心补丁

- 将 cgroup 更新相关的锁从具体调度类上提到 `kernel/sched/core.c`。
- 统一 cgroup 任务组更新（task group update）的临界区，减少重复加锁与竞态。

## 状态与讨论

- 当前状态：**under_review**（v3）。
- 持续性系列（往日已发 v1/v2），本期为 v3 修订。

## 关联

- 001 / 003 sched_ext cgroup 相关能力
- 009 sched/fair： cpufreq 压力
