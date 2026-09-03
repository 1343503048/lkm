---
title: "RFC PATCH v2：NUMA 细粒度均衡 + sched/cache 任务迁移辅助（23 补丁）"
date: 2026-09-02
tags: [sched/cache, load_balance]
series: "rfc v2 numa fine balance sched cache helpers"
type: feature
severity: medium
status: under_review
lore: ""
---

## 概述

这是一个较大的 RFC 系列（v2，共 23 个补丁），方向是 **NUMA 细粒度均衡** 与
**sched/cache 任务迁移决策辅助**。邮件中可见的子补丁讨论：02/23 引入具有唯一距离值的
NUMA distance matrix（UID 73108）、11/23 引入任务迁移决策的辅助函数（72903/72950）、
17/23 细粒度 NUMA 均衡（73045）。

## 改动内容 / 核心补丁（已见子补丁主题）

- 02/23 `sched/topology: Introduce a NUMA distance matrix with unique distance values`
- 11/23 `sched/cache: Introduce helpers for task migration decisions`
- 17/23 `sched/fair: Fine-granularity NUMA balancing`
- （其余补丁构成 NUMA 距离建模 + 迁移决策 + 细粒度均衡的完整框架）

## 状态与讨论

- 当前状态：**under_review / RFC 阶段**（v2，体量很大，需多轮评审）。
- 合入可能性 low/medium（大 RFC，方向上与 cache-aware 调度、NUMA balancing 演进一致，
  但需解决建模与开销争议）。
- 与 003（sched/cache use-after-free）、007（task_h_load）同属调度核心演进。

## 关联

- 003 sched/cache use-after-free mm 访问
- 007 sched/fair 重做 task_h_load
