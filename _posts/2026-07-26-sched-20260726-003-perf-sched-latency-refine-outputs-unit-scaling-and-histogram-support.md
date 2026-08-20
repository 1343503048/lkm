---
subject: 'perf sched: Suppress latency table output when trace samples are missing'
id: sched-20260726-003
date: 2026-07-26
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <uid-630@qq-imap>
lore_url: unknown
authors:
- Aaron Tomlin
maintainers_involved:
- Ian Rogers
current_version: v3
patch_series:
- version: v1
  msgid: unknown
  date: 2026-07-24
  summary: 改进 perf sched latency：修复空表输出、增加单位自适应缩放、加入延迟直方图。
  review_outcome: Ian Rogers 指出 latency_bucket() 存在整数溢出。
- version: v2
  msgid: unknown
  date: 2026-07-25
  summary: 修复 v1 的整数溢出问题。
  review_outcome: 继续收到对齐、swapper 过滤、--time 边界状态机等细节反馈。
- version: v3
  msgid: <uid-630@qq-imap>
  date: 2026-07-26
  summary: 对齐竖线分隔符、从 global_hist 排除 swapper 空闲线程、跨 --time 边界保留任务状态机、无匹配样本时抑制空表头并输出提示语。
  review_outcome: 逐条回应 v2 review，工具类改进，趋于成熟。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 perf tools 维护者对 v3 的最终确认，无明显阻塞项
contribution_opportunities:
- kind: testing
  description: 在真实工作负载的 perf.data 上试用 --histogram / --hist-mode / --time，验证单位自适应与直方图分桶的可读性，回帖使用反馈
- kind: review
  description: review builtin-sched.c 中直方图分桶与单位缩放逻辑的边界处理
generated_at: '2026-07-27T01:10:00'
source_email_count: 1
related_articles: []
tags:
- sched_debug
- perf
title: 'perf sched: Suppress latency table output when trace samples are missing'
layout: article
---

## TL;DR
Aaron Tomlin 改进 `perf sched latency` 的第 3 版：修复缺少 tracepoint 时误报成功的 bug、为延迟/运行时列做单位自适应缩放（ns/us/ms/s）、新增延迟直方图与时间区间过滤。属于 perf 工具侧的可用性增强，已迭代到 v3、逐条回应了 review，合入可能性较高。

## 背景与问题
`perf sched latency` 存在几个可用性问题：其一，当 perf.data 缺少所需 tracepoint 事件导致 `perf_session__has_traces()` 失败时，代码会 fall through 并返回成功（0），打印出空表头和全零统计，误导用户；其二，所有数值无条件按毫秒格式化，微秒级或秒级延迟难以阅读；其三，缺少直方图这类直观的分布可视化和按时间段过滤的能力。

## 技术方案
Patch 1：在缺少 tracepoint 时提前返回合适的错误码，不再输出误导性空表。Patch 2：对 Runtime/Avg delay/Max delay 三列按数值大小动态选择最合适单位（ns/us/ms/s）并同步更新表头。Patch 3：新增三个命令行选项——`--histogram(-H)` 输出 ASCII 延迟柱状图、`--hist-mode` 选择对数或 100us 等宽线性分桶、`--time` 限定处理的时间区间；并处理了无匹配样本时输出 "No matching trace samples found." 而非空图表。设计上把展示层改进与过滤能力解耦成独立 patch，便于分别 review。

## 版本演进与当前进展
v1 发出后 Ian Rogers 发现 `latency_bucket()` 整数溢出；v2 修复该溢出；v3 进一步做了竖线对齐、从 global_hist 排除 swapper 空闲线程、跨 `--time` 边界保留任务状态机转换、并抑制无样本时的空表头/总计/直方图。当前 v3，属逐版收敛细节的成熟阶段。

## Maintainer 意见与讨论焦点
主要 reviewer 为 Ian Rogers，集中在数值正确性（整数溢出）与输出细节（对齐、空表处理、idle 线程是否计入）。这些意见都在后续版本被逐条采纳，未见方向性分歧或 NAK。

## 合入评估
合入可能性较高。纯 perf 用户态工具改进，风险低，作者对 review 响应积极，v3 已无明显阻塞项，主要等待 perf tools 维护者最终确认。

## 效果评估
本系列是可读性/功能增强，不涉及内核运行时性能，邮件未给出、也不需要性能回退/提升数字。改进效果体现在输出正确性与可读性（避免误报、单位自适应、直方图），属功能性收益。

## 我可以参与的点
- 在真实负载的 perf.data 上试用新选项，验证单位自适应与直方图分桶可读性并回帖反馈
- review 直方图分桶与单位缩放逻辑的边界处理

## 参考链接
- lore thread: 未获取到（v2: 20260725173341.679782-1-atomlin@atomlin.com，v1: 20260724142901.634761-1-atomlin@atomlin.com，均为邮件正文引用）
- tip-bot commit: 未获取到
- stable backport: 未获取到
