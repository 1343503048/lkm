---
subject: 'sched/cache: Fix a thread aggregation conflict when there is one runnable
  task'
id: sched-20260810-010
date: 2026-08-10
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260810xxxxxx-chenyu@kernel.org>
lore_url: 未获取到
authors:
- Chen Yu
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Dietmar Eggemann
- Lu Wang
current_version: v2
patch_series:
- version: v2
  msgid: <20260810xxxxxx-chenyu@kernel.org>
  date: 2026-08-10
  summary: v2：修复当某 LLC 内仅有一个可运行任务时，active load balance（LLB）把该唯一任务错误地聚合/搬移，造成线程冲突与不必要的迁移。
  review_outcome: v2 发出，等待维护者对 LLB 唯一可运行任务判定的反馈。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待维护者确认 LLB 在「单可运行任务」场景的判定条件。
contribution_opportunities:
- kind: review
  description: 评审 active LB 在单可运行任务场景的跳过/搬移条件。
- kind: testing
  description: 构造 LLC 内单任务场景验证不再被错误聚合迁移。
generated_at: '2026-08-11T00:15:00'
source_email_count: 1
related_articles:
- sched-20260809-002
tags:
- sched/cache
- sched/fair
title: 'sched/cache: Fix a thread aggregation conflict when there is one runnable
  task'
layout: article
---

## TL;DR
Chen Yu 提交 v2「sched/cache: Fix a thread aggregation conflict when there is one runnable task」。修复 active load balance 在 LLC 内仅有一个可运行任务时的错误聚合/搬移。under_review。

## 背景与问题
LLC（last-level cache）域的 active load balance 用于把过载 CPU 的任务搬到其他 LLC。但当某个 LLC 域内仅有一个可运行任务、且该任务正独占运行时，原逻辑可能误判并进行「线程聚合」式搬移，反而造成冲突与不必要的迁移开销。

## 技术方案
在 active LB 的 LLC 判定中，识别「域内仅一个可运行任务」的情况，跳过会引入聚合冲突的搬移，避免把唯一任务错误地移走。设计取舍：保守处理单任务场景，优先保持局部性而非盲从均衡。

## 版本演进与当前进展
当前 v2（与 08-09 的 002「sched/cache 尊重 migrate_llc_task」同主题但独立修复点）。8/10 发出。

## Maintainer 意见与讨论焦点
焦点：单可运行任务判定的精确条件，以及是否与 migrate_llc_task 语义叠加。

## 合入评估
合入可能性 medium。属缓存局部性相关的均衡修复。

## 效果评估
无 benchmark；预期减少不必要的跨 LLC 迁移。

## 我可以参与的点
- 构造单任务 LLC 场景验证不再错误迁移；
- 评审与 002（migrate_llc_task）语义的协调。

## 参考链接
- lore: 未获取到
- 关联: sched-20260809-002
