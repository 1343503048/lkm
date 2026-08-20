---
id: sched-20260819-004
date: 2026-08-19
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: 未获取到
authors:
- Vladimir Zapolskiy
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-19
  summary: do_balance_callbacks() 中显式函数指针类型转换 (void (*)(struct rq *))head->func 是多余的——它不会改变
    struct balance_callback 成员 (*func) 的函数类型，直接删除该强制转换。
  review_outcome: v1 刚发出，暂无 review 意见。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 纯清理，等 maintainer ack
  next_action: 等待 Peter/Ingo 收下。
contribution_opportunities:
- kind: review
  description: 可帮忙 ack 这处 trivial 清理。
generated_at: '2026-08-20T00:30:00'
source_email_count: 1
related_articles: []
tags:
- sched/core
title: sched-20260819-004-sched-core-remove-balance-callback-cast
layout: article
---


## TL;DR
Vladimir Zapolskiy 移除 `do_balance_callbacks()` 中多余的函数指针类型转换，属 trivial 非功能清理。

## 背景与问题
`kernel/sched/core.c` 的 `do_balance_callbacks()` 用 `(void (*)(struct rq *))head->func` 做显式转换，但该转换并不改变 `struct balance_callback` 成员 `(*func)` 的函数类型，纯属冗余。

## 技术方案
删除该强制转换，直接 `func = head->func;`。改动 1 行（`kernel/sched/core.c | 2 +-`）。

## 版本演进与当前进展
v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无。

## 合入评估
合入可能性 high：trivial 清理，无功能影响，无阻塞。

## 效果评估
无功能变化，无性能数据（作者明确 "trivial and non-functional change"）。

## 我可以参与的点
- 可作为 reviewer 给出 ack。

## 参考链接
- lore thread: 未获取到
