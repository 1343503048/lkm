---
title: "sched, steal_governor v11：preferred CPU 相关补丁（讨论继续）"
date: 2026-09-02
tags: [sched/core, sched/fair, preempt]
series: "steal governor preferred cpus vcpu backoff"
type: feature
severity: medium
status: under_review
related_articles: ["sched-20260825-008-sched-steal-governor-v11.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-25 的文章）

steal_governor 系列（v11，引入 preferred CPUs 与 steal 驱动的 vCPU backoff）本期有
新的评审/讨论（Re: UID 73310，对应 v11 05/12 `sched/core: Try to use a preferred CPU
in is_cpu_allowed`）。

## 改动内容 / 核心补丁

- 延续 08-25 的 v11 系列：在 `is_cpu_allowed()` 中优先使用 preferred CPU、load balance
  仅在 preferred CPUs 间进行等。
- 本期为针对 05/12 等子补丁的评审交流，未见新版本号。

## 状态与讨论

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 合入可能性 medium（大系列，需多轮评审）。

## 关联

- 08-25 008 steal_governor v11 主文
- 001 Proxy Execution 批合并入（同属 guest/steal 调度方向）
