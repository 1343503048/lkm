---
id: sched-20260805-011
date: '2026-08-05'
title: 'perf sched latency: Refine outputs, unit scaling, and histogram support'
series: perf sched latency refinement
type: feature
status: under_review
severity: none
merge_likelihood: high
tags:
- perf
- sched_debug
authors:
- Namhyung Kim <namhyung@kernel.org>
reviewers:
- Arnaldo Carvalho de Melo <acme@kernel.org>
related_articles:
- sched-20260804-019
emails:
- uid-20515@qq-imap
layout: article
---

# perf sched latency: 细化延迟直方图与 swapper 处理

## 摘要

`perf sched latency` 的子命令用于按任务汇总调度延迟（从 wakeup 到 actually-on-CPU 的等待时间）。本系列对其做细化：改进延迟直方图的**分桶（bucket）策略**，并修正对 `swapper`（idle 任务，pid 0）的处理——此前 idle 任务被计入「延迟统计」会污染汇总，因为 swapper 的「等待」并不是真实调度延迟。

本日要点（20515）：
- Namhyung 调整直方图分桶，使其在对数尺度上更均匀（如 1us / 10us / 100us / 1ms / 10ms 边界），并支持按 `--sort` 选择按 avg / max / count 排序。
- 对 `swapper`/`idle` 任务：在 `perf_sched__latency` 的聚合里显式跳过 pid 0，或在输出中标为 `(idle)` 并单独成组，避免其巨大 count 掩盖真实任务的尾部延迟。
- 与 08-04-019（v7 中位数/swapper）的衔接：本日继续打磨 swapper 的展示口径，使其既不污染统计、又保留「idle 占用了多少调度机会」的可观测性。

## 技术细节

`perf sched latency` 数据流：从 `perf.data` 的 sched:sched_wakeup / sched_switch 事件重建每个任务的 `wakeup→switch_in` 间隔，累加进直方图。

改动（示意）：
```
if (task->pid == 0) {            // swapper
    idle_stats.count++;
    continue;                    // 不进任务延迟直方图
}
histogram_insert(task, delta);
```

直方图分桶从固定线性改为对数边界，使长尾延迟（ms 级）不再被压在最后一个桶里看不清分布。

## 影响与风险

- 影响面：仅 `perf sched latency` 的用户态工具输出，不影响内核调度。
- 风险：低。纯工具侧改动；需注意与旧有脚本解析输出格式的兼容性（分桶标签变化可能影响下游解析）。
- 收益：更准确的延迟分布视图，避免 idle 任务污染真实任务的尾部延迟分析。

## 评价

工具可观测性增强，与 08-04-019 同系列延续。方向合理、reviewer（Arnaldo）已介入，合入可能性高。建议保留旧输出格式的可选兼容开关以免破坏既有脚本。
