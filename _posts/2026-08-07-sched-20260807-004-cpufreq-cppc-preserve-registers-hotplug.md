---
date: 2026-08-07
series: cpufreq-cppc-preserve-registers
version: v4
status: in-review
tags:
- cpufreq
- topology
related_articles: []
submitter: Sumit Gupta
emails:
- uid: 25518
  subject: '[PATCH v4 0/4] cpufreq: CPPC: Keep the policy across CPU hotplug'
- uid: 25519
  subject: '[PATCH v4 1/4] ... preserve OSPM set registers across hotplug'
- uid: 25521
  subject: '[PATCH v4 2/4] ... preserve across suspend/resume'
- uid: 25522
  subject: '[PATCH v4 3/4] ... cover/related'
title: 'cpufreq: CPPC 在热插拔/挂起恢复间保留 OSPM 设置的寄存器'
layout: article
---

## 概述

Sumit Gupta 提交 v4 的 4 片 CPPC cpufreq 系列，目标是在 CPU 热插拔与系统挂起/恢复周期之间，保留 OSPM（操作系统电源管理）设置的 CPPC 寄存器（如自动性能等级、最小/最大性能寄存器）。

## 背景与问题

CPPC 允许 OS 直接写性能寄存器来设定 CPU 的性能目标。但当前实现在以下场景会丢失这些设置：

- CPU 热插拔（offline/online）后，被重置。
- 系统 suspend/resume 后，寄存器恢复为固件默认值。

导致 policy（含 OSPM 设定的性能边界）在这些生命周期事件中丢失，影响性能一致性与能耗控制。

## 变更内容

v4 系列分 4 片：

1. 在 CPU 热插拔间保持 policy（0/4 cover）。
2. 跨 hotplug 保留 OSPM 设置的寄存器。
3. 跨 suspend/resume 保留 OSPM 设置的寄存器。
4. 相关收尾/清理。

## 状态

v4 迭代，处于评审阶段。

## 参考链接

- 系列：uid 25518 / 25519 / 25521 / 25522
