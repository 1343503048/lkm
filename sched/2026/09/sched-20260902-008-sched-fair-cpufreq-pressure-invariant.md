---
title: "sched/fair：仅在频率为不变量时施加 cpufreq 压力（讨论继续）"
date: 2026-09-02
tags: [schedutil, sched/fair, regression]
series: "cpufreq pressure invariant freq only"
type: fix
severity: medium
status: under_review
related_articles: ["sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md", "sched-20260825-006-sched-fair-cpufreq-pressure-invariant.md", "sched-20260826-003-sched-cpufreq-reevaluate-tickless-idle.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）

cpufreq 压力（cpufreq pressure）按「可达最高频率/当前可达最高频率」降 capacity，但
utilization 仅在频率不变（frequency invariant）架构才带匹配 scaling，导致语义不一致。
焦点集中在「是否仅在不 invariant 场景施加 pressure」。

本期（Re: UID 73378 / 73396 / 73507）为讨论继续，未见新版本号或新基准数据，主要围绕
实现细节与正确性论证。

## 改动内容 / 核心补丁

- 延续此前方向：将 cpufreq 压力施加范围限制到「频率为不变量」的场景。
- 避免在非不变平台上产生误导性的利用率压缩。

## 状态与讨论

- 当前状态：**under_review / 讨论中**（增量更新，无新版本）。
- 合入可能性 medium。

## 关联

- 003 sched/cache use-after-free、002 PREEMPT_DYNAMIC（同属调度核心活跃话题）
