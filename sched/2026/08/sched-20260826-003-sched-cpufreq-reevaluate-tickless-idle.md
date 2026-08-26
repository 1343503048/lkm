---
title: "sched/cpufreq：进入 tickless idle 前重新评估频率（讨论继续）"
date: 2026-08-26
tags: [schedutil, sched/fair, compatibility]
series: "reevaluate cpufreq before tickless idle"
type: fix
severity: medium
status: under_review
related_articles: ["sched-20260825-005-sched-cpufreq-reevaluate-tickless-idle.md", "sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）

在走向 tickless idle（NOHZ idle）的路径上，于最终决定 idle 前主动重新评估一次频率
（cpufreq 压力/利用率更新），减少 idle 进出过程中因频率评估滞后带来的延迟与能耗浪费。

本期（Re: UID 57872）为该系列的评审/讨论继续（+此前 08-25 的 56442/56820/57349），
未见新的版本号或基准数据，主要围绕实现细节与合入条件交流。

## 改动内容 / 核心补丁

- 延续此前方案：在 tickless idle 判定前调用一次频率重新评估。
- 本期讨论聚焦与 `schedutil`、cpufreq 压力机制的衔接细节。

## 状态与讨论

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 与 004（sched/fair 仅在不变量频处施加 cpufreq 压力，08-24/25 讨论）共同围绕
  cpufreq 压力与频率评估准确性展开，但场景不同。

## 关联

- 004（同日无新邮件）/ 08-24/25 相关 cpufreq pressure 系列
