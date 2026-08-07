---
title: "perf/core: 修复 sched_task() 在纯 CPU-wide 事件下 NULL pmu_ctx 解引用"
date: 2026-08-07
series: "perf-core-sched-task-cpu-wide"
version: "v6"
status: "in-review"
tags: [perf, sched/core, crash]
related_articles: []
submitter: "Puranjay Mohan"
emails:
  - uid: 27034
    subject: "Re: [PATCH v6 3/3] perf/core: Fix NULL pmu_ctx passed to pmu->sched_task()"
  - uid: 26563
    subject: "[PATCH v6 2/3] ... Run sched_task() for PMUs with only CPU-wide events"
  - uid: 26587
    subject: "[PATCH v6 1/3] ... sched_task() dispatch and branch entry fixes"
---

## 概述

Puranjay Mohan 在 v6 中提交一组 perf/core 修复，解决 `pmu->sched_task()` 回调在上下文切换时被传入 NULL `pmu_ctx`、以及纯 CPU-wide 事件 PMU 的 `sched_task()` 永不运行的问题（与 BRBE/LBR 分支栈泄漏相关，Fixes `bd2756811766` "perf: Rewrite core context handling"）。

## 三片内容

1. **NULL pmu_ctx 修复**：`perf_pmu_sched_task()` 在 `cpuctx->task_ctx` 被设置时提前返回，而 `cpc->task_epc` 仅在任务上下文被调度进该 CPU 时非 NULL，因此 `__perf_pmu_sched_task()` 始终传入 NULL。表现为 armv8pmu_sched_task() 的 NULL 解引用 oops（需 BRBE，v6.17 引入）。最初以三元表达式 `cpc->task_epc ?: &cpc->epc` 修复，经 Peter Zijlstra 评审后确认应直接传 `&cpc->epc`（v7 修正）。

2. **纯 CPU-wide 事件 PMU**：`perf_pmu_sched_task()` 提前返回后将工作留给 `perf_ctx_sched_task_cb()`，后者只遍历 `ctx->pmu_ctx_list`，因此"事件全为 CPU-wide"的 PMU 永不被访问，`sched_task()` 不运行。用 `perf record -b -e cycles -a -- ls` 时每切到带自身 perf 事件的 task 就跳过 armv8pmu_sched_task()，BRBE 记录跨 task 边界泄漏；x86 上 `intel_pmu_lbr_add()` 也无条件调用 `perf_sched_cb_inc()`，LBR 同样泄漏。修复：去掉提前返回，改为跳过 `perf_ctx_sched_task_cb()` 已处理的单个 CPC，并统一两者在 `cpc->task_epc` 上的门控。

3. **dispatch 与 branch entry 修复**：三处修复最初为给 arm64 的 `bpf_get_branch_snapshot()` 加 BRBE 支持而发现，独立成系列（版本号沿用）。

## 状态

v6，已获 Usama Arif `Acked-by`；第 1 片在讨论中确认将于 v7 简化为直接传 `&cpc->epc`。

## 参考链接

- 讨论：uid 27034 / 26563 / 26587
