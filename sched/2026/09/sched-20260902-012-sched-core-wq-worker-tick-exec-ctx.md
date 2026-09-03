---
title: "sched/core：为执行上下文调用 wq_worker_tick()"
date: 2026-09-02
tags: [sched/core]
series: "sched core wq worker tick exec context"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

工作队列（workqueue）worker 的节流/记账依赖 `wq_worker_tick()` 在合适时机被调用。
本期（UID 74505）提出在「执行上下文（execution context）」路径上也调用
`wq_worker_tick()`，使 worker 的 tick 记账在更多执行场景下保持一致。

## 改动内容 / 核心补丁

- `sched/core: Call wq_worker_tick() for the execution context`：在调度核心的执行上下文
  相关路径补上 `wq_worker_tick()` 调用。

## 状态与讨论

- 当前状态：**under_review**（新补丁）。
- 合入可能性 medium；影响 workqueue 节流记账准确性，需确认无副作用。

## 关联

- 002 sched/core 清理（同属调度核心活跃改动）
