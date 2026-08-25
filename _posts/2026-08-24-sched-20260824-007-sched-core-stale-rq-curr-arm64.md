---
title: sched-20260824-007-sched-core-stale-rq-curr-arm64
date: 2026-08-24
tags:
- crash
- sched/core
series: stale rq->curr arm64
type: bug
severity: critical
status: under_review
lore: ''
layout: article
---

## 概述

在 arm64 平台上偶发地观测到运行队列 `rq->curr` 指向已过期/无效的任务，引发
后续调度判断或统计异常（UID 54429）。该问题可能与抢占、上下文切换或远程核
更新 rq->curr 的时序有关。

## 改动内容 / 核心补丁

- 提供崩溃/异常现场与触发条件（多为偶发、与特定负载/核间交互相关）。
- 讨论 rq->curr 在跨核更新与抢占路径上的一致性保障。

## 状态与讨论

- 当前状态：**under_review / 报告阶段**。
- 与 006（v4.19 厂商内核崩溃）同属“运行队列状态一致性”类问题，但本例面向 arm64
  与更主线场景。

## 关联

- 006 sched/fair：v4.19 NULL deref
- 008 sched/core：推迟被抢占远端 vCPU task clock 更新
