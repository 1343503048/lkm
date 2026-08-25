# 从 RT 优先级队列 `struct cpupri_vec` 中删除未使用的 `count` 字段


## TL;DR
从 RT 优先级队列 `struct cpupri_vec` 中删除未使用的 `count` 字段，纯死代码清理。

## 背景与问题
`kernel/sched/cpupri.c` 的 `struct cpupri_vec` 含 `count` 字段，已无任何代码引用（早期 UP 计数语义遗留）。属代码质量清理。

## 技术方案
直接移除 `count` 字段定义及任何残留引用。

## 版本演进与当前进展
v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无。

## 合入评估
合入可能性 high：trivial 死代码清理，无功能影响，无阻塞。

## 效果评估
无功能变化，无性能数据。

## 我可以参与的点
- 可 review 确认 `count` 全树无引用后给出 ack。

## 参考链接
- lore thread: 未获取到

---
id: sched-20260819-006
date: 2026-08-19
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors: [unknown]
maintainers_involved: [Peter Zijlstra, Juri Lelli, Ingo Molnar]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-19
    summary: "从 struct cpupri_vec 中删除 count 字段。该字段未被使用（早期 UP 计数用途已无引用），属死代码清理。"
    review_outcome: "v1 刚发出，暂无 review 意见。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["纯清理，等 maintainer ack"]
  next_action: "等待 RT 维护者收下。"
contribution_opportunities:
  - kind: review
    description: "可帮忙确认 count 字段确实无其它引用后 ack。"
generated_at: "2026-08-20T00:30:00"
source_email_count: 1
related_articles: []
tags: [rt, sched/core]
---
