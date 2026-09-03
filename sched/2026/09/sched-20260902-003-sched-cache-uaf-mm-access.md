---
title: "sched/cache：修复 account_mm_sched() 中访问被替换 mm 的 use-after-free"
date: 2026-09-02
tags: [sched/cache, crash]
series: "sched cache use after free mm access"
type: bug
severity: high
status: under_review
lore: ""
---

## 概述

`sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务
被 `exec` 替换掉 `mm` 后，旧 `mm` 可能已被释放，若仍持有引用访问即触发
use-after-free（UAF）。相关讨论（Re: UID 72357）已指出该问题。

## 改动内容 / 核心补丁

系列 `sched/cache: Fix use after free mm access in account_mm_sched()`（UID 72573 0/2
封面）：
- 1/2 `sched/cache: Decouple sched_cache_group from mm`（72574）：把调度缓存组与 `mm`
  解耦，不再依赖可能被替换的 `mm`。
- 2/2 `sched/cache: Introduce task_struct->sched_cache_grp`（72578）：在 `task_struct`
  上直接引入 `sched_cache_grp` 字段，避免使用已释放的 `mm` 派生信息。

## 状态与讨论

- 当前状态：**under_review**（新系列，0/2 封面 + 2 个实现补丁）。
- 严重度：**high**（UAF 属内存安全类 bug，可能导致崩溃/数据损坏）。
- 合入可能性 medium；属调度缓存（LLC 亲和）方向，与 09 系列 sched/cache 工作相关。

## 关联

- 009 RFC v2 NUMA 细粒度均衡 + sched/cache 迁移辅助（同属 sched/cache 方向）
