---
title: "sched, steal_governor：引入 preferred CPUs 与 steal 驱动的 vCPU backoff（v11）"
date: 2026-08-25
tags: [sched/core, sched/fair, preempt]
series: "steal governor preferred cpus vcpu backoff"
type: feature
severity: medium
status: under_review
lore: ""
---

## 概述

steal_governor 系列（v11，UID 57064 00/12 等共 12 个补丁）引入「preferred CPUs」
概念与「steal 驱动的 vCPU backoff」：在虚拟化/steal 时间显著的场景下，让任务更倾向
停留在 preferred CPU 上，并对被 host 抢占（steal）的 vCPU 做后退（backoff），以降低
跨 CPU 迁移与抢占总开销。

v11 包含的支撑补丁（据封面与各子补丁主题）：
- 05/12 `sched/core`: Try to use a preferred CPU in `is_cpu_allowed`
- 06/12 `sched/fair`: Load balance only among preferred CPUs
- 07/12 `sched/core`: Push current task from non preferred CPU
- 08/12 `sched/debug`: Add migration stats due to non preferred CPUs
- 02/12 `sched/docs`: Document cpu_preferred_mask and Preferred CPU concept
- 01/12 `sched/cputime`: Add `kcpustat_field_total` helper（已获 Yury Norov、Mete Durlu Reviewed-by）

`kcpustat_field_total` helper（UID 57064 正文可见）：在指定 cpumask 上对某一类
cpustat 求和，简化 s390 hiperdispatch 与 proc/uptime 的 steal/idle 累计，并被后续
steal governor 补丁复用。

## 改动内容 / 核心补丁

- 引入 `cpu_preferred_mask` 与 Preferred CPU 概念，并文档化。
- `is_cpu_allowed` 优先用 preferred CPU；load balance 仅在 preferred CPUs 间进行；
  从非 preferred CPU 上 push 当前任务；新增相关迁移统计。
- 提供 `kcpustat_field_total()` 辅助函数（已评审通过）。

## 状态与讨论

- 当前状态：**under_review**（v11，体量较大，已迭代多轮）。
- 与 008（前日 RFC defer 被抢占远端 vCPU task clock）同属「guest/steal 调度记账」
  主题，但本系列更宏观（preferred CPU + backoff 治理）；两者可能互补。
- 合入可能性 medium（大系列，需多轮评审）。

## 关联

- 008 sched/core+KVM：推迟被抢占远端 vCPU task clock 更新（RFC，前日）
- 010 sched：sched/debug per-CPU debugfs 文件（v5）
