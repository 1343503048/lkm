# sched fair is core idle check all cpus

## 概述

Mete Durlu 修改 `is_core_idle()`，使其在判断核心是否空闲时检查核心内**所有** CPU（含被传入评估的 CPU 本身），而非跳过该 CPU。

## 问题

原实现在评估 `idle_cpu()` 时会跳过传入的 CPU。`is_core_idle()` 因此无法正确判断"整个核心（含传入 CPU）是否空闲"。在 `sched_balance_newidle()` 中 `env->dst_cpu == this_cpu`，且处于 `__schedule()` 中 `rq->curr` 仍是 outgoing task，导致：
- `idle_cpu(this_cpu)` 为 false；
- 每个 newidle balance 都得到 `env->dst_core_idle == false`，使 misfit gate 停止拉取、asym packing 不再适用。

## 评审关注

Peter Zijlstra（Re）指出该 skip 的存在正是为了让调用方能从"即将变为 idle"的 CPU 询问，此时 `idle_cpu()` 尚不能为 true。移除 skip 会影响 newidle balance 的 misfit/asym 行为；s390 无法复现（因 `SD_ASYM_PACKING` 仅 powerpc/x86 ITMT 设，`SD_ASYM_CPUCAPACITY` 仅 arm64 big.LITTLE/x86 hybrid 设）。其他调用者（numa_idle_core、select_idle_capacity 等）也需重新评估。

## 状态

处于评审/讨论阶段，需权衡对 newidle balance 与其他调用者的影响。

## 参考链接

- 邮件：uid 25338 / 26028

---
subject: "sched/fair: 让 is_core_idle() 检查核心内所有 CPU"
date: 2026-08-07
series: "sched-fair-is-core-idle"
version: "v1"
status: "in-review"
tags: [sched/fair, idle, topology]
related_articles: []
submitter: "Mete Durlu"
emails:
  - uid: 25338
    subject: "[PATCH] sched/fair: make is_core_idle() check all CPUs in a core"
  - uid: 26028
    subject: "Re: [PATCH] sched/fair: make is_core_idle() check all CPUs in a core"
---
