---
subject: 'sched/fair: 非对称容量域负载均衡改进（已合入 tip/sched/core）'
date: 2026-08-08
series: sched-fair-asym-capacity-load-balance
version: v1
status: merged
tags:
- sched/fair
- load_balance
- topology
related_articles: []
submitter: Ricardo Neri (Intel)
emails:
- uid: 28230
  subject: '[tip: sched/core] sched/topology: Restore SD_PREFER_SIBLING in domains
    with asymmetric capacity'
- uid: 28231
  subject: '[tip: sched/core] sched/fair: Allow load balancing between CPUs of identical
    capacity'
- uid: 28232
  subject: '[tip: sched/core] sched/fair: Do not skip CPUs of similar capacity with
    busy SMT siblings'
- uid: 28233
  subject: '[tip: sched/core] sched/fair: Check CPU capacity before comparing group
    types during load balance'
- uid: 28235
  subject: '[tip: sched/core] sched/fair: Skip misfit load accounting when the destination
    CPU cannot help'
- uid: 28236
  subject: '[tip: sched/core] sched/fair: Also gate overloaded status update for SD_ASYM_CPUCAPACITY'
title: 'sched/fair: Do not skip CPUs of similar capacity with busy SMT siblings'
layout: article
---

## 概述

一批 sched/fair 的非对称容量（asymmetric capacity / `SD_ASYM_CPUCAPACITY`，如 big.LITTLE、x86 hybrid）负载均衡改进由 tip-bot2 合并进 **tip/sched/core** 分支。作者主要为 Ricardo Neri（Intel），含 Peter Zijlstra 等。

## 合入的 patch 集

- **sched/topology: Restore SD_PREFER_SIBLING in domains with asymmetric capacity**（28230）：在含非对称容量的域中恢复 `SD_PREFER_SIBLING` 标志。该标志把共享-LLC 域的负载均衡从"均衡空闲 CPU 数"转为"均衡运行任务数"，使 newly-idle 负载均衡可在 cluster 间迁移（outgoing 任务已出队但 CPU 尚未转 idle）。
- **sched/fair: Allow load balancing between CPUs of identical capacity**（28231）：允许相同容量的 CPU 间负载均衡。
- **sched/fair: Do not skip CPUs of similar capacity with busy SMT siblings**（28232）：不跳过具有相似容量但 SMT 兄弟繁忙的 CPU。
- **sched/fair: Check CPU capacity before comparing group types during load balance**（28233）：在 LB 比较组类型前先检查 CPU 容量。
- **sched/fair: Skip misfit load accounting when the destination CPU cannot help**（28235）：当目标 CPU 无法提供帮助时跳过 misfit 记账（misfit 消失后仍可在有富余容量时把高 util 任务迁到更大 CPU）。
- **sched/fair: Also gate overloaded status update for SD_ASYM_CPUCAPACITY**（28236）：对非对称容量域同样门控 overloaded 状态更新。

## 状态

**已合入 tip/sched/core**（commit 经 tip-bot2 合并）。属调度域构建与负载均衡正确性/效率改进，主要惠及 ARM big.LITTLE 与 x86 hybrid 拓扑。

## 参考链接

- tip 合并通知：uid 28230 / 28231 / 28232 / 28233 / 28235 / 28236
