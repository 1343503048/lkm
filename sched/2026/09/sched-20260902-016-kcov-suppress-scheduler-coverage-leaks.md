---
title: "kcov：抑制定时器与调度器覆盖泄漏"
date: 2026-09-02
tags: [sched/core, documentation]
series: "kcov suppress scheduler coverage leaks"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

kcov（内核覆盖率工具）在调度器与定时器相关路径上会产生「覆盖泄漏」——即不应被采集的
上下文（如调度器内部、定时器软中断）被计入覆盖率，污染 fuzzing/覆盖率结果。本期
（v2，UID 73544 `0/6` Re:）提出抑制这类泄漏。

## 改动内容 / 核心补丁

- `[PATCH v2 0/6] kcov: Suppress timer and scheduler coverage leaks`：在定时器与调度器
  相关路径上抑制 kcov 的覆盖采集，使覆盖率聚焦于被测逻辑。

## 状态与讨论

- 当前状态：**under_review**（v2，6 补丁系列）。
- 合入可能性 medium；属工具/可观测性改进，与调度器路径有交集。

## 关联

- 002 sched/core 清理（同属调度核心活跃改动）
