# perf sched latency: Refine outputs, unit scaling, and histogram support

## 概述

Aaron Tomlin 的 `perf sched latency` v9 系列获 Namhyung Kim 回复 **"Applied to perf-tools-next, thanks!"**，标志着该工具改进已合入 perf 工具树。

## 改进内容

- 抑制误导性的空表输出（当 `perf_session__has_traces()` 因 perf.data 缺少 tracepoint 事件而失败时，`perf sched latency` 原会穿透并返回成功(0)，渲染空表头与归零统计）。
- 扩展 pipe 模式流处理。
- 引入延迟与运行时统计的**动态单位自动缩放**（dynamic unit auto-scaling）。
- 新增**延迟直方图可视化**与时间段过滤（time-span filtering）。
- `map_switch_event()` 中的 `thread__get_runtime()` 增加 NULL 指针解引用防护（内存分配失败时）。

## 状态

**已合入 perf-tools-next**（工具侧，非内核调度核心）。这是 perf 用户态工具改进，与内核 sched 子系统交互有限，但属调度可观测性范畴。

## 参考链接

- 合入确认回帖：uid 27929（Namhyung Kim）

---
subject: "perf sched latency: v9 改进已合入 perf-tools-next"
date: 2026-08-08
series: "perf-sched-latency-v9"
version: "v9"
status: "merged"
tags: [perf]
related_articles: [sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx]
submitter: "Aaron Tomlin"
emails:
  - uid: 27929
    subject: "Re: [PATCH v9 0/4] perf sched latency: Refine outputs, unit scaling, and histogram support"
---
