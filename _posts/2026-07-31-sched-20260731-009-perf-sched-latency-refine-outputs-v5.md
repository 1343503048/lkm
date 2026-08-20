---
id: sched-20260731-009
date: 2026-07-31
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260730185416.97166-1-atomlin@atomlin.com>
lore_url: https://lore.kernel.org/lkml/20260730185416.97166-1-atomlin@atomlin.com
authors:
- Adrian Hunter
maintainers_involved: []
current_version: v5
patch_series:
- version: v5
  msgid: <20260730185416.97166-1-atomlin@atomlin.com>
  date: 2026-07-30
  summary: perf sched latency 三项改进：修复空表格输出、动态单位自动缩放、延迟直方图可视化
  review_outcome: v5 刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 perf 维护者 review
contribution_opportunities:
- kind: testing
  description: 使用 perf sched latency 测试不同工作负载，验证单位缩放和直方图功能
generated_at: '2026-07-31T16:30:00'
source_email_count: 3
related_articles:
- sched-20260730-007
tags:
- sched_debug
- perf
title: perf sched latency refine outputs v5
layout: article
---

## TL;DR

本文为增量更新，完整背景见 sched-20260730-007。Adrian Hunter 的 perf sched latency 改进系列推进到 v5，包含三项改进：修复空表格输出、动态单位自动缩放（ns/us/ms/s）、延迟直方图可视化（--histogram/-H、--hist-mode、--time 选项）。v5 刚发出，暂无新 review。

## 背景与问题

（完整背景见 sched-20260730-007）`perf sched latency` 存在以下问题：
1. 缺少 tracepoint 时仍输出空表格和零值统计
2. 所有值统一以 ms 显示，微秒或秒级延迟难以阅读
3. 缺少延迟分布可视化

## 技术方案（v5）

**Patch 1/3** — 修复空表格输出：
- 支持 pipe mode 流：注册缺失的回调（.attr, .tracing_data, .build_id, .feature）
- handlers 数组提升到文件作用域的 `latency_handlers[]`
- 增加内存分配失败的 NULL 指针保护

**Patch 2/3** — 动态单位自动缩放：
- Runtime、Avg delay、Max delay 列自动选择最合适单位（ns/us/ms/s）
- 列标题动态更新，格式说明符对齐

**Patch 3/3** — 直方图与时间过滤：
- `--histogram (-H)`: ASCII 柱状图显示 CPU 等待延迟分布
- `--hist-mode`: 对数（log）或 100us 等宽线性（linear）分桶
- `--time`: 按时间范围过滤事件

## 版本演进与当前进展

- **v5**（2026-07-30）：当前版本，pipe mode 支持增强

## Maintainer 意见与讨论焦点

暂无新的 review 意见。

## 合入评估

- **likelihood: medium** — perf 工具改进，需要 perf 维护者 review
- **next_action**: 等待 review

## 效果评估

暂无效果数据。工具可用性改进。

## 我可以参与的点

- **测试新功能**：使用 `--histogram`、`--hist-mode`、`--time` 选项测试不同工作负载，验证单位缩放和直方图功能的正确性和实用性

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260730185416.97166-1-atomlin@atomlin.com
- 前日分析: sched-20260730-007
