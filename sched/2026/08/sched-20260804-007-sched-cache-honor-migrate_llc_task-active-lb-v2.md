---
id: sched-20260804-007
date: 2026-08-04
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Lu Wang]
maintainers_involved: [Peter Zijlstra, Vincent Guittot]
current_version: v4
patch_series:
  - version: v4
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "active load balance 应尊重 migrate_llc_task（仅本地 LLC 内迁移）语义。延续 08-03-005：Peter Zijlstra 要求把 can_migrate_llc_task() 合入 task_can_migrate() 由 active LB 复用，消除两条路径语义分叉。"
    review_outcome: "Peter Zijlstra 给出代码级重构意见，方向认可，待作者按反馈发 v5。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["待作者按 PeterZ 的 helper 合并意见发 v5"]
  next_action: "等待 v5（can_migrate_llc_task() 合入 task_can_migrate()）后合入。"
contribution_opportunities:
  - kind: review
    description: "v5 发布后审阅 can_migrate_llc_task() 合并进 task_can_migrate() 是否改变了 nohz/stop 等其它调用点的迁移行为，回帖确认无回归（08-03-005 已提过）。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: ["sched-20260803-005-sched-cache-honor-migrate_llc_task-semantics-in-active-load-balance"]
tags: [cfs, load_balance, affinity]
---

# sched/cache: active LB 尊重 migrate_llc_task（v4→v5 推进）

## TL;DR
active load balance 未尊重 `migrate_llc_task`（仅本地 LLC 内迁移）语义的修复在 08-04 推进到 v4，Peter Zijlstra 要求把 LLC 语义 helper 合入 `task_can_migrate()` 消除两条路径分叉。这是 08-03-005 的延续，合入可能性 high。

## 背景与问题
`migrate_llc_task` 要求任务仅在自身本地 LLC 内迁移，但 active LB 走 `can_migrate_task()` 只查 `!migration_disabled`，会忽略该约束。详见 08-03-005。

## 技术方案
引入 `can_migrate_llc_task()`，v4 中 Peter Zijlstra 进一步要求把它放进 `task_can_migrate()` 由 active LB 复用，从而消除 `can_migrate_task()` 与 active LB 两条迁移检查路径的语义分歧。

## 版本演进与当前进展
- 08-03：v4 基础（08-03-005）。
- 08-04：Peter Zijlstra 给出明确重构意见，待作者发 v5。

## Maintainer 意见与讨论焦点
Peter Zijlstra：明确「合并 helper 消除歧义」，属实现整洁性+正确性，非方向反对。

## 合入评估
合入可能性 high。正确性+重构修正，等 v5 即可。

## 效果评估
无 benchmark；属缓存局部性与策略正确性修复。

## 我可以参与的点
- v5 发布后审阅 helper 合并是否改变其它调用点（nohz/stop）迁移行为，回帖回归确认。

## 参考链接
- 08-03 文章：sched-20260803-005-sched-cache-honor-migrate_llc_task-semantics-in-active-load-balance
