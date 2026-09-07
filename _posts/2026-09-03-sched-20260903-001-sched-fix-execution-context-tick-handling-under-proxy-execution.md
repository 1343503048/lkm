---
id: sched-20260903-001
date: '2026-09-03'
subject: 'sched: Fix execution-context tick handling under proxy execution'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+Fix+execution-context+tick+handling+under+proxy+execution
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- Hui Su
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 2
related_articles:
- sched-20260902-012
tags:
- sched/core
- sched/fair
- sched/cache
- proxy_execution
title: 'sched: Fix execution-context tick handling under proxy execution'
layout: article
---

## TL;DR

代理执行（proxy execution）把调度上下文（rq->donor）与执行上下文（rq->curr）分离。目前作者 Hui Su，v2（封面 + numa/cache 两 patch），并附带独立的 wq_worker_tick() 修正 patch。

## 背景与问题

代理执行（proxy execution）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）分离。周期性 tick 中仍有部分记账/扫描以 donor 触发，导致 NUMA 周期扫描、`cache` 任务 tick、以及 workqueue 的 `wq_worker_tick()` 都基于「`sum_exec_runtime` 未被代理执行推进」的 donor 任务，造成 NUMA 扫描错位、cache tick 错配与 kworker 记账丢失。本系列把这几类周期行为改到基于 `rq->curr` 的真实执行上下文。

## 技术方案

- `sched/numa`：`task_tick_numa()` 改用 `rq->curr` 的执行上下文驱动周期 NUMA 扫描并排队 `numa_work`（v2 标题 "Drive NUMA task tick from execution context"，早期版本 "Use execution context for NUMA task tick"）。
- `sched/cache`：`cache` 任务 tick 同理改用执行上下文（"Drive cache task tick from execution context"）。
- `sched/core`：`wq_worker_tick()` 用 `rq->curr` 调用，修复代理执行下 kworker 替 donor 执行时 workqueue CPU 时间记账丢失、`WORKER_CPU_INTENSIVE` 处理延迟与 pool 并发管理滞后。

## 版本演进与当前进展

- 作者 Hui Su，v2（封面 + numa/cache 两 patch），并附带独立的 `wq_worker_tick()` 修正 patch。
- 本日收到多封复审（Re）：围绕非 RT 执行任务借用 RT 带宽时 `rt.timeout` 的重置语义、以及 `cache` 任务 tick 在主动负载均衡中的配合。
- 属「代理执行执行上下文修正」主线，与同日 005/008 同源。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260902-012]] wq_worker_tick 执行上下文初版（本系列为其后续复审）。
  - proxy execution 主线（sched/core 合入后的一系列上下文一致性修复）。
- 相关代码/commit：
  - `kernel/sched/fair.c` `task_tick_fair` / `task_tick_numa`
  - `kernel/sched/core.c` `wq_worker_tick()` 调用点
