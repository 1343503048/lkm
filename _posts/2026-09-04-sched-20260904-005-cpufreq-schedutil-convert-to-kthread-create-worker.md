---
id: sched-20260904-005
date: '2026-09-04'
subject: 'cpufreq: schedutil: convert to kthread_create_worker'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=cpufreq+schedutil+convert+to+kthread_create_worker
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Bradley Morgan
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
- cpufreq
- schedutil
- sched/core
title: 'cpufreq: schedutil: convert to kthread_create_worker'
layout: article
---

## TL;DR

将 cpufreq_schedutil（位于 kernel/sched/cpufreq_schedutil.c）从废弃的 kthread_run(kthread_worker_fn) 模式改用 kthread_create_worker()。目前作者 Bradley Morgan，v2 4/5。- 纯清理/modernization，无行为变更意图。

## 背景与问题

将 `cpufreq_schedutil`（位于 `kernel/sched/cpufreq_schedutil.c`）从废弃的 `kthread_run(kthread_worker_fn)` 模式改用 `kthread_create_worker()`。新 API 在 worker 启动前设置 `worker->task`，规避旧模式潜在的竞态。

## 技术方案

- `kernel/sched/cpufreq_schedutil.c` 33 行改动，替换 worker 创建方式。
- 属 5 补丁系列 v2 的第 4 个（v2 4/5）。

## 版本演进与当前进展

- 作者 Bradley Morgan，v2 4/5。
- 纯清理/modernization，无行为变更意图。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关代码/commit：
  - `kernel/sched/cpufreq_schedutil.c`
