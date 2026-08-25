---
title: "sched：用专用 per-CPU 计数器替换 nr_pinned 偏移 hack（RFC）"
date: 2026-08-25
tags: [sched/core, rt]
series: "replace nr_pinned offset per-cpu counter"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

调度器内部通过 `nr_pinned` 偏移（在某个计数结构里借用偏移）来跟踪 per-rq 的 pinned
任务数，属于一种脆弱的 hack。本期 RFC（UID 56401 0/1、56402 1/1）提议用专用的
per-CPU 计数器替换这一偏移 hack，使语义更清晰、避免与其它字段复用带来的耦合。

## 改动内容 / 核心补丁

- 新增专用 per-CPU 计数器来维护 nr_pinned（pinned 任务计数）。
- 移除原有基于偏移复用的实现，简化相关读/写路径。

## 状态与讨论

- 当前状态：**under_review / RFC 阶段**。
- 属于调度核心的清理/健壮性改进，影响 rt/fair 的 pinned 计数逻辑；需确认与
  active balance、migration 路径的交互。

## 关联

- 010 sched：sched/debug 引入 per-CPU debugfs 文件（v5）
