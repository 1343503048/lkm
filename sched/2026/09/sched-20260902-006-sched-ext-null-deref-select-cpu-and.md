---
title: "sched_ext：修复 select_cpu_and 子调度错误路径的 NULL sched 解引用"
date: 2026-09-02
tags: [sched_ext, crash]
series: "sched ext null deref select cpu and"
type: bug
severity: high
status: under_review
lore: ""
---

## 概述

`sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
指针做充分空值检查，导致在错误分支上解引用空指针（NULL deref）崩溃（UID 74497）。

## 改动内容 / 核心补丁

- `sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path`：在
  select_cpu_and 的子调度错误返回路径上补上空指针判断，避免解引用空 `sched`。

## 状态与讨论

- 当前状态：**under_review**（新补丁）。
- 严重度：**high**（空指针解引用属崩溃类 bug）。
- 合入可能性 medium/high；属明确的小修复。

## 关联

- 004 sched_ext：拒绝 NMI 调用会拿锁 kfuncs
- 005 sched_ext：文档化并强制 vtime 排序约束
