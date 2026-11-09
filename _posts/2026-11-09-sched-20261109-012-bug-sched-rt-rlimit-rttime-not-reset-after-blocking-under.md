---
id: sched-20261109-012
date: '2026-11-09'
subject: 'sched/rt: RLIMIT_RTTIME not reset after blocking under SCHED_OTHER'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <CALcE18MKy0KbTC=mb0ir-g7g_YaN5AzPS=9MELTW84tyw0JemQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CALcE18MKy0KbTC=mb0ir-g7g_YaN5AzPS=9MELTW84tyw0JemQ@mail.gmail.com/
authors:
- l I
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无人响应；需 RT 侧确认语义
  next_action: 等 RT 维护者确认，社区补修复补丁
contribution_opportunities:
- kind: review
  description: 核对 rt.c 的 RLIMIT_RTTIME 复位逻辑，确认切出 RT class 后阻塞不复位的根因
- kind: new_patch
  description: 补一个「切出 SCHED_FIFO/RR 时复位 rt runtime」的修复补丁并附回归
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- rt
- rt_bandwidth
title: 'sched/rt: RLIMIT_RTTIME not reset after blocking under SCHED_OTHER'
layout: article
---

## TL;DR

社区报告一个 RT 调度 bug：任务从 SCHED_FIFO 切到 SCHED_OTHER 并阻塞睡眠后，RLIMIT_RTTIME 的 RT 运行时间计数器没有复位——反复「FIFO 跑 8ms → 切 SCHED_OTHER → 睡眠 10ms」会让 RT runtime 跨睡眠累计，最终触发 SIGXCPU，即便每次 RT 执行区间都低于限制。附完整 reproducer，Ubuntu 7.0.0-38-generic 复现，源码检查 mainline 同样存在。当日无人回帖。

## 背景与问题

RLIMIT_RTTIME 限制 SCHED_FIFO/SCHED_RR 任务的连续 RT 运行时长，POSIX 语义下任务阻塞（睡眠）时应复位 RT runtime 计数器。报告者发现：任务 SCHED_FIFO → SCHED_OTHER 切换后阻塞（nanosleep）不会复位该计数器，导致 RT runtime 跨睡眠累计；循环 80 次（每次 8ms FIFO + 10ms 睡眠）后进程被 SIGXCPU 杀死，即使每次 RT 区间（8ms）远低于 soft 50ms / hard 200ms 限制。源码检查表明 mainline 存在同样的缺失复位。

## 技术方案

当日为 [BUG] 报告，无补丁。报告者给出完整 reproducer（`setrlimit(RLIMIT_RTTIME, {50ms, 200ms})` + 循环 `sched_setscheduler(SCHED_FIFO)` 跑 8ms → `SCHED_OTHER` → `nanosleep(10ms)`），并标注「阻塞睡眠应复位 RT runtime 计数器」的期望行为。根因方向：RT runtime 复位（`sched_rt_runtime_exceeded`/`update_curr_rt` 相关路径）未覆盖「切出 RT class 后阻塞」的情形。

## 版本演进与当前进展

*current_version: null（单封 [BUG] 报告，无补丁）*。2026-11-09 发出，当日无人回帖。

## Maintainer 意见与讨论焦点

当日无维护者回帖。报告者非补丁提交者，仅提供复现与源码级判断。无 NAK、无分歧。

## 合入评估

*likelihood=unknown*。刚报告、无人响应，是否确认为 bug、归属（rt_bandwidth 记账）与修法均待定。*blocking_issues*：① 无人响应；② 需 RT 侧（Steven Rostedt/Sebastian Andrzej Siewior 或 rt_bandwidth 维护者）确认语义。*next_action*：等 RT 维护者确认是否属 bug，作者/社区补修复补丁。

## 效果评估

报告者用 reproducer 实测 80 次循环后被 SIGXCPU 杀死（行为错误），无修复后数据。严重度评估：非崩溃，但会导致 RT 任务被错误 SIGXCPU，影响依赖 RLIMIT_RTTIME 的实时应用。

## 我可以参与的点

- **review**：核对 `kernel/sched/rt.c` 中 RLIMIT_RTTIME 复位逻辑（`sched_rt_runtime_exceeded` 与 class 切换路径），确认「切出 RT class 后阻塞不复位」的根因。
- **new_patch**：若确认是 bug，可补一个「切出 SCHED_FIFO/RR 时复位 rt runtime」的修复补丁（附 reproducer 回归）。

## 参考链接

- lore thread: https://lore.kernel.org/all/CALcE18MKy0KbTC=mb0ir-g7g_YaN5AzPS=9MELTW84tyw0JemQ@mail.gmail.com/
