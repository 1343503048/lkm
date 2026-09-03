---
title: "sched：移除 sched_class::balance()（7/7 系列）"
date: 2026-09-02
tags: [sched/core, load_balance]
series: "remove sched class balance"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

调度类（sched_class）的 `balance()` 回调历史上用于某个调度类的负载均衡钩子，但现代
实现下已不再需要或被更通用的路径取代。本期（作为 7/7 系列的一部分，Re: UID 72566
对应 `7/7`）移除 `sched_class::balance()`，清理这一遗留接口。

## 改动内容 / 核心补丁

- `[PATCH 7/7] sched: Remove sched_class::balance()`（UID 72566 Re:），属 7 补丁系列
  的最后一步清理。
- 同日还有相关 `2/7` 的 Re: `sched/core: Simplify/fix time updates`（UID 72934）。

## 状态与讨论

- 当前状态：**under_review**（作为多补丁系列的一部分推进）。
- 合入可能性 medium/high；纯清理，风险低。

## 关联

- 002 PREEMPT_DYNAMIC 简化 + static key 迁移（同属调度核心清理）
- 007 sched/fair 重做 task_h_load（同属负载均衡相关）
