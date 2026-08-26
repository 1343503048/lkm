---
id: sched-20260826-003
date: 2026-08-26
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: unknown
lore_url: unknown
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: RFC 文档补丁，为 WF_SYNC 在 CFS wakeup 路径中的放置语义补充文档
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待调度维护者 review 文档准确性
contribution_opportunities:
- kind: review
  description: Review 文档内容是否与实际代码行为一致
generated_at: '2026-08-27T01:14:00'
source_email_count: 1
related_articles: []
tags:
- cfs
title: 'sched: Document WF_SYNC wakeup placement semantics'
layout: article
---

## TL;DR

Shubhang Kaushik (Ampere) 提交 RFC 文档补丁，为 `WF_SYNC` 在 CFS wakeup 路径中的放置语义补充文档。新增 `Documentation/scheduler/sched-wake-affinity.rst`，明确记录 `WF_SYNC` 不绕过 `wake_wide()`、不使 `wake_affine()` 的目标成为最终决定、不要求 wakee 立即抢占。纯文档补丁，无代码行为变更。

## 背景与问题

`WF_SYNC` 由期望 waker 很快调度离开的调用者提供。CFS 的 wakeup 路径将其用作启发式指标，但其放置和抢占行为从未被文档化。开发者在理解 `WF_SYNC` 的实际效果时容易产生误解——例如以为它会强制 wakee 抢占当前任务，或保证 wakee 被放在 waker 的 CPU 上。

## 技术方案

新增 `sched-wake-affinity.rst` 文档，从 `try_to_wake_up()` 开始，经过 `select_task_rq_fair()`、`select_idle_sibling()` 到 `preempt_sync()`，完整记录 `WF_SYNC` 的行为链路：

- `WF_SYNC` 不绕过 `wake_wide()` 的启发式检查
- `wake_affine()` 的目标 CPU 并非最终决定
- 不要求 wakee 立即抢占当前运行任务

这是纯文档化现有行为，不引入新的放置策略。

## 版本演进与当前进展

v1 RFC 刚发出，暂无 review 意见。这是 2 篇系列中的第 1 篇。

## Maintainer 意见与讨论焦点

暂无 review 意见。

## 合入评估

- **likelihood**: medium（纯文档补丁，方向正确，但 RFC 性质意味着可能需要迭代）
- **blocking_issues**: 无
- **next_action**: 等待调度子系统维护者 review 文档的准确性

## 效果评估

暂无效果数据（纯文档补丁）。

## 我可以参与的点

- 可以 review 文档内容是否与实际代码行为一致，特别是 `WF_SYNC` 在 `select_idle_sibling()` 中的交互
- 如果有特定场景下 `WF_SYNC` 行为不符合文档描述的情况，可以反馈

## 参考链接

- lore thread: 未获取到
