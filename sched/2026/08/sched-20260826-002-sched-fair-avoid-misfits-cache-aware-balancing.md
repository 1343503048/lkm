---
title: "sched/fair：cache-aware 负载均衡时避免产生 misfit 任务"
date: 2026-08-26
tags: [sched/fair, sched/cache, load_balance]
series: "avoid misfits cache-aware balancing"
type: fix
severity: medium
status: under_review
lore: ""
---

## 概述

cache-aware scheduling（考虑 LLC/缓存域的负载均衡）在选核与迁移时，可能把任务放到
一个「容量/缓存亲和」不匹配的 CPU 上，从而把该任务标记为 misfit（小核上的大任务等），
触发后续的 misfit 迁移逻辑，反而增加抖动与迁移开销。本期（UID 57854，含 Re: 59700）
提出在 cache-aware balancing 路径中避免产生这类本可避免的 misfit。

## 改动内容 / 核心补丁

- 在 cache-aware balancing 的选核/迁移判定中加入 misfit 规避逻辑，避免在关心缓存
  局部性的同时制造新的 misfit 任务。
- 目标：在缓存局部性收益与 misfit 迁移成本之间取得更优平衡。

## 状态与讨论

- 当前状态：**under_review**（原始补丁 UID 57854；Re: 59700 为评审交流）。
- 与 08-24/25 的 `sched/cache: active load balance 尊重 migrate_llc_task`（010）同属
  cache-aware 调度方向的持续改进。

## 关联

- 08-24 010 sched/cache：active load balance 尊重 migrate_llc_task
- 007 PROXY_EXEC 备选方案（同为调度核心改动）
