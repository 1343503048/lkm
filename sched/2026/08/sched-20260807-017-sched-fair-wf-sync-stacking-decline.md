---
title: "sched/fair: 当 waker 的 LLC 是瓶颈时拒绝 WF_SYNC 堆叠"
date: 2026-08-07
series: "sched-fair-wf-sync-stacking"
version: "v1"
status: "in-review"
tags: [sched/fair, affinity, load_balance]
related_articles: []
submitter: "Vinicius Costa Gomes"
emails:
  - uid: 25787
    subject: "[PATCH RFC] sched/fair: decline WF_SYNC stacking when waker LLC is the bottleneck"
  - uid: 25778
    subject: "Re: [PATCH RFC] sched/fair: decline WF_SYNC stacking when waker LLC is the bottleneck"
  - uid: 25281
    subject: "Re: [PATCH RFC] sched/fair: decline WF_SYNC stacking when waker LLC is the bottleneck"
  - uid: 26097
    subject: "Re: [PATCH RFC] sched/fair: decline WF_SYNC stacking when waker LLC is the bottleneck"
---

## 概述

Vinicius Costa Gomes 提交 RFC，修正自 commit `900bbaae67e9`（"epoll: Add synchronous wakeup support for ep_poll_callback"）以来 epoll 驱动的 `WF_SYNC` 唤醒"过强"的问题：任务会堆叠在繁忙的 NUMA 节点上，而其他节点相对空闲。

## 问题

`WF_SYNC` 的"堆叠到 waker"快捷路径未考虑 LLC 负载，导致 openresty 类工作负载（指标为尾延迟）在 CWF SNC3 单 socket 系统上出现一个节点过载、其余空闲的回归。将 NIC RX 中断分散到所有 NUMA 节点、或 revert `900bbaae67e9` 均有助于缓解，但 revert 不可取（因该 commit 改善了真实负载）。

## 修复思路

使 `WF_SYNC` 的"堆叠到 waker"快捷路径考虑 this 与 prev 的 LLC 负载，仅当 waker（this）的 LLC 完全满载且 prev 的 LLC 比 waker 更轻时，才**拒绝**该快捷路径（即不再堆叠）。讨论中有建议使用 IRQ 分散等替代方案（因为把 EEVDF 卸载出去是好的）。

## 状态

RFC，处于讨论阶段。

## 参考链接

- 邮件：uid 25787 / 25778 / 25281 / 26097
