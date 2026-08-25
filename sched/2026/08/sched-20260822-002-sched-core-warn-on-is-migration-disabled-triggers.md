# `sched/core: WARN_ON(is_migration_disabled())` 触发告警

## TL;DR

`sched/core: WARN_ON(is_migration_disabled())` 触发告警，表明任务在迁移被禁用时出现了意外的调度路径。需要调查触发条件。

## 背景与问题

`is_migration_disabled()` 检查任务的迁移是否被禁用。当此 WARN_ON 触发时，意味着调度器在任务迁移禁用状态下走了不应该走的路径。

## 技术方案

需要分析触发条件，确定是哪条代码路径在迁移禁用时错误地尝试迁移任务。

## 版本演进与当前进展

Bug 报告刚发出，暂无回复。

## Maintainer 意见与讨论焦点

暂无回复。

## 合入评估

- **likelihood**: unknown
- **blocking_issues**: 需要复现和分析
- **next_action**: 等待社区分析

## 效果评估

暂无数据。

## 我可以参与的点

- 如果有复现环境，可以帮忙收集触发条件信息
- 分析调度路径中迁移禁用的处理逻辑

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260822-002
date: 2026-08-22
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: "未获取到"
lore_url: "未获取到"
authors: ["unknown"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "未获取到"
    date: 2026-08-22
    summary: "WARN_ON(is_migration_disabled()) 触发告警"
    review_outcome: "暂无回复"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "需要复现和分析"
  next_action: "等待社区分析触发条件"
contribution_opportunities:
  - kind: discussion
    description: "帮助分析迁移禁用状态下的调度路径"
generated_at: "2026-08-22T10:00:00"
source_email_count: 1
related_articles: []
tags: ["sched/core", "migration"]
---
