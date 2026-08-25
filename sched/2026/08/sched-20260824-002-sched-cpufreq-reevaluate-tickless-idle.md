## 概述

在进入 tickless idle（NOHZ idle）之前，调度器与 cpufreq 之间的协调存在窗口：
当前可能在尚未根据最新负载重新评估频率的情况下就进入 idle，导致退出 idle 或
周边任务的频率策略不够及时。本补丁（UID 55237）拟在进入 tickless idle 前主动
重新评估一次频率。

## 改动内容 / 核心补丁

- 在走向 tickless idle 的路径上，于最终决定 idle 前调用一次频率重新评估
  （cpufreq 压力/利用率更新）。
- 目标：减少 idle 进出过程中因频率评估滞后带来的延迟与能耗浪费。

## 状态与讨论

- 当前状态：**under_review**。
- 与 004（sched/fair 仅在不变量频处施加 cpufreq 压力）主题相关，二者都围绕
  cpufreq 压力与频率评估的准确性展开，但分别针对不同场景。

## 关联

- 004 sched/fair：仅在频率为不变量时施加 cpufreq 压力
- 009 sched：将 cgroup 更新锁上提到 core

---
title: "sched/cpufreq：进入 tickless idle 前重新评估频率"
date: 2026-08-24
tags: [schedutil, sched/fair, compatibility]
series: "reevaluate cpufreq before tickless idle"
type: fix
severity: medium
status: under_review
lore: ""
---
