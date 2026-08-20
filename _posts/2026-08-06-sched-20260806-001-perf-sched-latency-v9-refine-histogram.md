---
id: sched-20260806-001
date: '2026-08-06'
title: 'perf sched latency: Refine outputs, unit scaling, and histogram support'
series: 'perf sched latency: Refine outputs, unit scaling, histogram'
type: feature
status: under_review
severity: none
merge_likelihood: high
tags:
- perf
- sched_debug
authors:
- Aaron Tomlin <atomlin@atomlin.com>
- Namhyung Kim <namhyung@kernel.org>
- Ian Rogers <irogers@google.com>
- Arnaldo Carvalho de Melo <acme@kernel.org>
reviewers:
- Ian Rogers <irogers@google.com>
- Namhyung Kim <namhyung@kernel.org>
related_articles:
- sched-20260805-011
emails:
- uid-24961@qq-imap
- uid-24963@qq-imap
- uid-24971@qq-imap
- uid-24958@qq-imap
layout: article
---

# perf sched latency: v9 细化输出、单位自动缩放与直方图支持

## 摘要

Aaron Tomlin 的 `perf sched latency` 改进系列推进到 **v9**（4 个 patch），目标收尾工具侧的可读性与可用性。本日可见 v9 0/4 cover（24961）及若干 review（Namhyung/Ian 已给 R-b）。

四个 patch：
1. 修复 `perf_session__has_traces()` 失败时仍「成功返回 0」导致渲染空表/清零统计的问题；并对 `thread__get_runtime()` 做 NULL 兜底。
2. 扩展 pipe 模式流处理（动态注册 .attr/.tracing_data/.build_id/.feature 回调，handler 数组提升为 file-scope，按 evsel 动态分配 handler）。
3. 引入动态单位自动缩放（Runtime/Avg delay/Max delay 按 ns/us/ms/s 自适应，列头与格式对齐）。
4. 新增 `--histogram (-H)`（CPU 等待延迟 ASCII 柱状图）、`--hist-mode`（log / 100us 线性分桶）、`--time`（按 [start,stop] 时间窗过滤）。

本日要点：v9 仅新增 Ian 的 Reviewed-by 并 rebase 到 perf-tools-next；Namhyung 在本系列历史中已要求「swapper(idle) 不进直方图」「--time 不破坏跨边界的唤醒状态机」「补 shell 测试」等，均已落实。

## 技术细节

关键修正点（示意）：
```
// patch1：has_traces 失败应早退而非 fall through
if (!perf_session__has_traces(session, "sched"))
    return -1;            // 原实现 fall-through 返回 0
// patch3：动态单位
scale = pick_unit(max_val);   // ns/us/ms/s
snprintf(col, ..., "%*.2f%s", width, val/unit_div, unit_suffix);
// patch4：直方图分桶
if (hist_mode == LOG) log_bucket(delta); else linear_100us_bucket(delta);
```

swapper 处理：用 `thread__tid(...) != 0` 整数判断替代字符串比较，从 global_hist 桶中排除 idle 线程。

## 影响与风险

- 影响面：仅 `perf sched latency` 用户态工具，不影响内核调度。
- 风险：低。纯工具改动；需关注输出格式变化对既有脚本的兼容（v9 已用 tabular 对齐 + 自动单位，下游解析需注意）。
- 收益：延迟分布更易读（自动单位 + 直方图），pipe 模式不再丢事件，空数据不再渲染误导性的空表。

## 评价

工具可观测性增强，已过多轮打磨（v1→v9），reviewer（Namhyung/Ian/Arnaldo）深度介入，合入可能性高。建议通过后进入 perf-tools-next。
