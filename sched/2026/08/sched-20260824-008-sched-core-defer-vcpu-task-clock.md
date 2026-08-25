## 概述

当远端 vCPU 被抢占时，其 task clock 的更新若立即进行会带来额外的跨核开销与
统计偏差。RFC 系列（UID 54073 RFC 2/2、UID 54074 RFC 0/2，含 KVM stealtime 关联）
提议推迟（defer）被抢占远端 vCPU 的 task clock 更新，待合适时机批量/本地处理。

## 改动内容 / 核心补丁

- (RFC 0/2) 说明动机：guest 调度记账（stealtime）与 task clock 在跨核抢占场景下
  存在记账不准确与开销问题。
- (RFC 2/2) 在 sched/core 中实现“推迟被抢占远端 vCPU task clock 更新”的机制，
  配合 KVM stealtime 修正 guest 视角的调度时间。

## 状态与讨论

- 当前状态：**under_review / RFC 阶段**。
- 实测示例（来自 RFC 0/2 正文）：在 16 vCPU guest + hammered 64 线程压测下，
  hackbench 时延 0.436s → 0.405s、Unix sock 0.051s → 0.040s、Pipe 0.041s → 0.035s，
  context_switch 11.5M → 10.5M，sys 时间 8.5s → 5.7s，整体开销下降。

## 关联

- 007 sched/core：stale rq->curr
- 002 / 004 cpufreq 与频率/压力评估

---
title: "sched/core + KVM：推迟被抢占的远端 vCPU task clock 更新（RFC）"
date: 2026-08-24
tags: [preempt, sched/core, proxy_execution]
series: "defer preempted remote vcpu task clock"
type: fix
severity: medium
status: under_review
lore: ""
---
