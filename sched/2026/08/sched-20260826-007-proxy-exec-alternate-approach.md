---
title: "sched/core：PROXY_EXEC 的备选方案 —— 睡眠属主处理的另一思路（RFC PoC）"
date: 2026-08-26
tags: [proxy_execution, sched/core]
series: "proxy execution alternate sleeping-owner approach"
type: feature
severity: medium
status: under_review
lore: ""
---

## 概述

Proxy Execution（PE，用于解决优先级翻转/锁持有者代理运行）的既有实现依赖
`task_on_rq_migrating()` 与在 enqueue 路径上的特殊处理。本 RFC PoC（UID 58516 00/16
封面 + 16 个补丁）提出**另一种**睡眠属主（sleeping-owner）处理思路：把「阻塞任务的
激活」拆成独立 helper，并用 `p->is_linked` 跟踪任务是否挂在 sleeping owner 上，配合
MIGRATING 标志与 chain-wakeup 机制，在 enqueue 路径上实现 proxy activation。

首补丁（据 58516 正文）新增 `activate_blocked_task()` helper（激活 `!p->on_rq ||
p->se.sched_delayed` 的阻塞任务），把 `task_on_rq_migrating()` 在 sched_class 回调
enqueue 路径上的用法清理出来，为「在 enqueue 路径上做 proxy 激活」铺路；声明「无功能
变更」。

## 改动内容 / 核心补丁（16 补丁要点）

- 01/16 把阻塞任务激活拆成 `activate_blocked_task()` helper。
- 02/16 用 enqueue/dequeue flags 替代 `task_on_rq_migrating()`。
- 03/16 `sched/fair` 在 `update_load_avg()` 的 DO_ATTACH 用 enqueue flags。
- 04/16 未找到 owner 时激活 blocked donor。
- 05/16 不把阻塞 donor 排在 delayed owner 上。
- 06/16 将阻塞 donor 排到 sleeping owner 上以支持 chain-wakeup。
- 07/16 避免把阻塞 donor 排到 sleeping owner 上时发生延迟。
- 08/16 `sched/deadline` 为带 MIGRATING 标志的阻塞/proxy 激活做准备。
- 09/16 跟踪任务被阻塞时的 CPU。
- 10/16 引入 `p->is_linked` 跟踪是否挂在 sleeping owner 上。
- 11/16 在 wakeup 时准备与 `->is_linked` 一起检查 `->on_rq`。
- 12/16 在阻塞与激活 linked donors 时加上 MIGRATING 标志。
- 13/16 用 `p->is_linked` 状态尽早从 sleeping owner 解链。
- 14/16 引入 chain-wakeup 以激活阻塞 donor。
- 15/16（未列全）、16/16 把非 lock-holder 的激活设为 fast-path。

## 状态与讨论

- 当前状态：**under_review / RFC PoC**（体量较大，作者 K Prateek Nayak，尚处概念验证）。
- 与既有 PE 实现路线相对比，分歧点在于是否需要保留 `task_on_rq_migrating()` 语义；
  本方案试图用更显式的 `is_linked` + MIGRATING 标志来替代。合入可能性 medium（需多轮
  评审，且要与主线 PE 方向对齐）。
- 属长期演进方向，短期合入概率低。

## 关联

- 001 / 004 sched 核心注释与清理（同属 sched/core 改动）
