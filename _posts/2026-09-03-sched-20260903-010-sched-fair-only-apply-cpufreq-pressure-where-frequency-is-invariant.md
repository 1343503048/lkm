---
id: sched-20260903-010
date: '2026-09-03'
subject: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/fair+Only+apply+cpufreq+pressure+where+frequency+is+invariant
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Vincent Guittot
- Jianyong Wu
- Jianyong Wu
- Hongyan Xia
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 6
related_articles:
- sched-20260902-008
tags:
- cpufreq
- schedutil
- sched/fair
title: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
layout: article
---

## TL;DR

cpufreq 压力（cpu.capacity 因频率限制而下降）用于让调度器感知降频带来的算力损失。目前本日为复审（Re）讨论，围绕 invariant 判定的边界与 schedutil 交互。

## 背景与问题

cpufreq 压力（`cpu.capacity` 因频率限制而下降）用于让调度器感知降频带来的算力损失。本系列延续 09-02 的 cpufreq pressure 讨论：仅在频率「不变（invariant）」的 CPU 上施加 cpufreq 压力，避免在频率本身随负载变化的平台上重复/错误地折算算力，导致任务放置与频率选择相互放大。

## 技术方案

- 收紧 cpufreq pressure 的施加条件：仅当目标 CPU 的频率对算力折算是不变（invariant）时才计入压力，否则跳过。

## 版本演进与当前进展

- 本日为复审（Re）讨论，围绕 invariant 判定的边界与 schedutil 交互。
- 与 `sched-20260902-008` 同属 cpufreq pressure 系列。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260902-008]] cpufreq pressure invariant（讨论版）。
- 相关代码/commit：
  - `kernel/sched/fair.c` 算力/压力折算
  - `kernel/sched/cpufreq_schedutil.c`
