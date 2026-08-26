---
id: sched-20260825-011
date: 2026-08-25
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: unknown
lore_url: unknown
authors: []
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Peter Zijlstra 或 Ingo 捡起
contribution_opportunities: []
generated_at: '2026-08-27T10:00:00'
source_email_count: 1
related_articles: []
tags:
- eevdf
- cfs
title: 'sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers'
layout: article
---

## TL;DR

单 patch 修复，将 `sched/fair` 中剩余的 root cfs_rq 调用者统一使用 `update_curr_eevdf()` 而非旧接口。已获 Vincent Guittot Reviewed-by。

## 背景与问题

EEVDF 调度算法引入后，`update_curr_eevdf()` 是更新当前任务运行时间的标准接口。但部分 root cfs_rq 的调用路径仍在使用旧接口，导致行为不一致。

## 技术方案

将剩余的 root cfs_rq 调用者改为使用 `update_curr_eevdf()`，确保 EEVDF 的 vruntime 计算在所有路径上一致。

## 版本演进与当前进展

v1，已获 Vincent Guittot Reviewed-by。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**：Reviewed-by，无附加意见

## 合入评估

- **likelihood: high** — 已获 Vincent（sched/fair 维护者）Reviewed-by
- **blocking_issues**: 无
- **next_action**: 等待 Peter Zijlstra 或 Ingo 捡起

## 效果评估

暂无效果数据（正确性一致性修复）。

## 我可以参与的点

当前阶段已获 review，暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
