---
date: 2026-08-07
series: cpufreq-cppc-highest-perf
version: v5
status: in-review
tags:
- cpufreq
related_articles: []
submitter: Xueqin Luo
emails:
- uid: 26144
  subject: '[PATCH v5 1/3] cpufreq: CPPC: Add update_limits support for highest performance'
- uid: 26146
  subject: '[PATCH v5 2/3] cpufreq: CPPC: Refactor autonomous perf bounds into helper'
title: 'cpufreq: CPPC 最高性能寄存器与 update_limits 支持'
layout: article
---

## 概述

Xueqin Luo 提交 v5 的 CPPC cpufreq 系列（3 片），为 CPPC 的"最高性能"（highest performance）寄存器增加 `update_limits` 支持，并将自主性能边界（autonomous perf bounds）重构为辅助函数。

## 变更内容

1. **Add update_limits support for highest performance**：让 CPPC 驱动在 `update_limits` 路径中处理 highest performance 寄存器的变化，使动态更新（如平台电源/散热策略调整性能上限）能及时反映到 policy。
2. **Refactor autonomous perf bounds into helper**：将自主性能边界的设置逻辑抽取为辅助函数，减少重复并便于复用。

## 状态

v5 迭代，与 Sumit Gupta 的 "preserve registers" 系列同属 CPPC 改进方向但由不同作者推进，处于评审阶段。

## 参考链接

- 系列：uid 26144 / 26146
