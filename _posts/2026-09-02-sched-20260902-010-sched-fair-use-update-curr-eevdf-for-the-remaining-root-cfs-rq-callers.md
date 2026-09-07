---
id: sched-20260902-010
date: '2026-09-02'
subject: 'sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Zhan Xusheng
- Vincent Guittot
- tip-bot2 for Zhan Xusheng
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 确认随 tip/sched/urgent 进入主线后无 EEVDF 行为变化
contribution_opportunities:
- 跟进 tip/sched/urgent 合并结果，回归 nohz_full 与 cgroup throttling 场景
source_email_count: 3
related_articles:
- sched-20260826-011-sched-fair-update-curr-eevdf-root-cfs-rq.md
- sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq.md
tags:
- sched/fair
- eevdf
title: 'sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers'
layout: article
---

## TL;DR

EEVDF 一致性清理——把剩余直接操作 root cfs_rq 的调用方统一走 `update_curr_eevdf()`——已合入
`tip/sched/urgent`（Commit-ID 1719d035a6fa，作者 Zhan Xusheng）。无功能变化，跟进价值低。

## 背景与问题

（本文为增量更新，完整背景见 related_articles 中 08-25/08-26 的文章）

EEVDF 路径中，仍有部分直接操作 `root cfs_rq` 的调用点未统一走 `update_curr_eevdf()`
的当前语义。此前提议把这些剩余调用方统一改为使用 `update_curr_eevdf()`。

**本期进展：该改动已合入 `tip/sched/urgent`**（UID 73123 `[tip: sched/urgent]`）。

## 技术方案

- `sched/fair: Use update_curr_eevdf() for the remaining root cfs_rq callers`（合入
  tip/sched/urgent）。

## 版本演进与当前进展

- 当前状态：**merged_tip**（已进入 `tip/sched/urgent`，将随紧急修复窗口进入主线）。
- 合入可能性：**high/已合入**。属 EEVDF 内部一致性清理，风险低。

## Maintainer 意见与讨论焦点

当天的相关邮件只有合入通知本身（73124，tip-bot2 for Zhan Xusheng，9/2 15:22）。此前 Vincent Guittot
的评审发生在 8 月下旬，不在当日缓存范围内，且缓存未保留正文，无法判断讨论中是否有分歧。从最终落到
`sched/urgent` 而非 `sched/core` 看，维护者把它按 fix 处理。

## 合入评估

**已合入** `tip/sched/urgent`，会随紧急修复窗口进主线，无卡点。

## 效果评估

无效果数据，也不该有——调用点统一属语义一致性整理，线程内无人报告行为或性能变化。

## 我可以参与的点

当前阶段无明显参与空间。可做的只有确认它进主线后 nohz_full / cgroup throttling 等会走
root cfs_rq 更新的路径上行为没有变化；若无异常不必主动回帖。

## 参考链接

- 08-26 011 同主题讨论（原处于 discussion/under_review，本期合入）
