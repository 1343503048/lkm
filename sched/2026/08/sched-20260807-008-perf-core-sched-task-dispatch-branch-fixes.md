# perf/core: sched_task() dispatch and branch entry fixes

## 概述

作为 "perf/core sched_task 修复" 系列的一部分，本片包含若干在给 arm64 的 `bpf_get_branch_snapshot()` 加 BRBE 支持过程中发现的修复（版本号沿用原 BRBE 系列，因 patch 不依赖 BRBE 而独立成篇）。

## 变更内容

- 修复 `__perf_pmu_sched_task()` 向 `pmu->sched_task()` 传入 NULL `pmu_ctx` 的问题（armv8pmu_sched_task() 是唯一解引用该参数的实现，故 oops 需要 BRBE）。
- 修复纯 CPU-wide 事件 PMU 的 `sched_task()` 不运行导致的分支栈（BRBE/LBR）跨 task 泄漏。

这些修复与同系列第 2/3 片共同构成对 commit `bd2756811766`（"perf: Rewrite core context handling"）引入回归的纠正。

## 状态

v6，处于评审阶段（与 007 系列同源）。

## 参考链接

- 邮件：uid 26425

---
subject: "perf/core: sched_task() dispatch 与 branch entry 修复"
date: 2026-08-07
series: "perf-core-sched-task-dispatch-branch"
version: "v6"
status: "in-review"
tags: [perf, sched/core]
related_articles: []
submitter: "Puranjay Mohan"
emails:
  - uid: 26425
    subject: "[PATCH v6 1/3] perf/core: sched_task() dispatch and branch entry fixes"
---
