---
title: "sched/cpufreq：进入 tickless idle 前重新评估频率（讨论继续）"
date: 2026-08-25
tags: [schedutil, sched/fair, compatibility]
series: "reevaluate cpufreq before tickless idle"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-24 的文章）

在走向 tickless idle（NOHZ idle）的路径上，于最终决定 idle 前主动重新评估一次
频率（cpufreq 压力/利用率更新），减少 idle 进出过程中因频率评估滞后带来的延迟与
能耗浪费。

本期（Re: UID 56442 / 56820 / 57349）为该系列的评审/讨论继续，未见新的版本号或
基准数据，主要围绕实现细节与合入条件交流。

## 改动内容 / 核心补丁

- 延续 08-24 的方案：在 tickless idle 判定前调用一次频率重新评估。
- 本期讨论聚焦与 `schedutil`、cpufreq 压力机制的衔接细节。

## 状态与讨论

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 与 006（sched/fair 仅在不变量频处施加 cpufreq 压力）共同围绕 cpufreq 压力与
  频率评估准确性展开，但场景不同。

## 关联

- 006 sched/fair：仅在频率为不变量时施加 cpufreq 压力（讨论继续）
- 002 / 004 sched_ext 相关
