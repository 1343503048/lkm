---
id: sched-20260806-005
date: '2026-08-06'
title: 'perf/core: sched_task() dispatch and branch entry fixes'
series: 'perf/core: sched_task() dispatch and branch entry fixes'
type: fix
status: under_review
severity: medium
merge_likelihood: high
tags:
- perf
- sched_debug
authors:
- Puranjay Mohan <puranjay@kernel.org>
reviewers:
- Peter Zijlstra <peterz@infradead.org>
related_articles: []
emails:
- uid-24755@qq-imap
- uid-24760@qq-imap
- uid-24761@qq-imap
layout: article
---

# perf/core: sched_task() 调度钩子的分发与分支记录修复（v6）

## 摘要

Puranjay Mohan 的 `perf/core` 三个修复推进到 **v6**（从 BRBE 支持系列中拆出独立提交）。这三个 fix 在给 arm64 加 `bpf_get_branch_snapshot()` 的 BRBE 支持时发现。

- **Patch 1**：`__perf_pmu_sched_task()` 不再把 NULL `pmu_ctx` 传给 `pmu->sched_task()`。`armv8pmu_sched_task()` 是唯一解引用该参数的实现，故需 BRBE 才会 oops。
- **Patch 2**：让 `perf_pmu_sched_task()` 也访问「事件全是 CPU-wide」的 PMU。当前只要被调度任务自己有 perf 事件就跳过这些 PMU，导致 `perf record -b -a` 下分支记录跨任务边界泄漏。`intel_pmu_lbr_add()` 无条件调 `perf_sched_cb_inc()`，故 x86 LBR 同样受影响。
- **Patch 3**：用单条 struct 赋值清空 `struct perf_branch_entry`（原 `perf_clear_branch_entry_bitfields()` 已漂移：`new_type`/`priv` 从未被清，`arm_pmuv3.c` 用 `kmalloc()` 分配 per-CPU branch stack）。

v6 变化：把 sched_task() fix 拆成 patch1+patch2（NULL 解引用与漏分发是两个不同可达性的 bug）；给 patch2 的 gate 加 `cpc->task_epc` 条件（v5 移除 early return 后两路径对「事件 pin 到别 CPU 的任务」都跑了，被新增的 `WARN_ON_ONCE()` 抓住）；patch1/2 标 stable；从 BRBE 系列独立，rebase 到 tip perf/core。

## 技术细节

v6 关键（示意）：
```
// patch2 gate
if (cpc->task_epc)                // 新增 gate，避免两路径重复运行
    perf_ctx_sched_task_cb(...);
// patch3
*br_entry = (struct perf_branch_entry){};   // 单条清空
```
测试：128 CPU arm64 + BRBE，跑 `perf record -b -a` 配合 pin 到不同 CPU 的任务事件，patch2 新增的 `WARN_ON_ONCE()` 数秒内触发（验证修复前 bug 可达）。

## 影响与风险

- 影响面：perf/core 的 `sched_task()` 调度钩子分发与分支记录；x86 LBR / arm64 BRBE 用户（`perf record -b -a`）直接受益。
- 风险：中。改动 perf 调度钩子路径，需确认 gate 条件不误伤正常 CPU-wide 事件统计；已标 stable，需在多架构验证。
- 收益：修复分支记录跨任务泄漏与 NULL 解引用，提升 `perf record -b` 数据正确性。

## 评价

扎实的 perf 修复（带 stable + WARN_ON 自验证），从 BRBE 系列独立后更聚焦。合入可能性高，建议进 tip/perf/core。
