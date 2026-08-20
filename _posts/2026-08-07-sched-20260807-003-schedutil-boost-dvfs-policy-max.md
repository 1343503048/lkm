---
subject: 'schedutil: 让 DVFS 请求可达 boost 频率上限'
date: 2026-08-07
series: schedutil-boost-dvfs
version: v1
status: in-review
tags:
- cpufreq
- schedutil
related_articles: []
submitter: Sibi Sankar / Ananthu C V
emails:
- uid: 27139
  subject: 'Re: [PATCH 2/2] sched/cpufreq: Update schedutil''s DVFS request to reach
    the boost ceiling'
- uid: 27085
  subject: 'Re: [PATCH 2/2] sched/cpufreq: Update schedutil''s DVFS request to reach
    the boost ceiling'
- uid: 27064
  subject: 'Re: [PATCH 1/2] cpufreq: Allow cpuinfo max to decrease when boost is disabled'
- uid: 26813
  subject: 'Re: [PATCH 1/2] cpufreq: Allow cpuinfo max to decrease when boost is disabled'
title: 'schedutil: 让 DVFS 请求可达 boost 频率上限'
layout: article
---

## 概述

由 Sibi Sankar（与 Ananthu C V 合作）提交的两片补丁，修复 schedutil 调控下系统开启 cpufreq boost 后实际频率"永远跑不到 boost 区间"的问题。

## 问题根因

`capacity_freq_ref`（经 `get_capacity_ref_freq()` 暴露给 schedutil）是 commit `9942cb22ea45` 引入的固定锚点，运行时不变。但 schedutil 在同一定点 plugged 进 `map_util_freq()`，而该函数在 `capacity_freq_ref` 处恰好饱和。

结果：开启 boost 的系统在 schedutil 负载下实质上永远不会运行在 boost 频率。

## 修复

第 1/2 片（cpufreq 侧，Ananthu C V）：移除 commit `538b0188da46`（"cpufreq: ACPI: Set cpuinfo.max_freq directly if max boost is known"）增加的"仅允许 cpuinfo max 增加"的护栏，使 cpuinfo max 始终由 frequency table 扫描推导。正确标记 boost 项的驱动不受影响（扫描在 boost 关闭时已排除它们）。

第 2/2 片（schedutil 侧）：将 `policy->max` 而不是固定的 `capacity_freq_ref` 接入 `map_util_freq()` 方程，使 DVFS 请求翻译到 cpufreq 驱动的真实上限。

## 评审

Vincent Guittot、Christian Loehle、Zhongqiu Han 等参与讨论，围绕 capacity_freq_ref 的语义与 cpuinfo max 护栏的移除边界交换意见。

## 状态

处于评审/讨论阶段。

## 参考链接

- 讨论线程：uid 27139 / 27085 / 27064 / 26813
