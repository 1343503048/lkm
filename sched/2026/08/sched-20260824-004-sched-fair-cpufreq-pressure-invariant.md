---
title: "sched/fair：仅在频率为不变量时施加 cpufreq 压力"
date: 2026-08-24
tags: [schedutil, sched/fair, regression]
series: "cpufreq pressure invariant freq only"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

cpufreq 压力（cpufreq pressure）用于向调度器反馈由于频率受限带来的算力损失。
此前在频率为非不变量（frequency not invariant）平台上也会施加压力，可能引入
不准确的利用率估计与回归。本线程（Re: UID 54189 / 55200）讨论将 cpufreq 压力
的施加范围限制到“频率为不变量”的场景。

## 改动内容 / 核心补丁

- 调整 cpufreq 压力的计算/传播条件，仅在频率是不变量时才计入压力。
- 避免在频率非不变平台上产生误导性的利用率压缩。

## 状态与讨论

- 当前状态：**under_review / 讨论中**（以 Re: 形式推进）。
- 属于持续性讨论（往日已有相关 RFC/补丁），本期为针对主线的回复与修订。

## 关联

- 002 sched/cpufreq：tickless idle 前重新评估频率
- 009 sched：cgroup 更新锁上提到 core
