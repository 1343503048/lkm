---
id: sched-20261113-017
subject: 'sched/rt: Do not account migrate-disabled tasks as pushable'
date: 2026-11-13
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <avXKCDm7NiVejDiF@techsingularity.net>
lore_url: https://lore.kernel.org/all/avXKCDm7NiVejDiF@techsingularity.net/
authors:
- Mel Gorman
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: 2026-11-11
  summary: 三补丁：RT pushable 记账排除 migrate-disabled 任务
  review_outcome: Steven Rostedt 建议折叠，Peter 建议对齐 deadline
- version: v2
  msgid: <20261112153120.GU1779021@noisy.programming.kicks-ass.net>
  date: 2026-11-12
  summary: 折叠为单补丁：入列条件加 && !is_migration_disabled(p)
  review_outcome: Peter 问副作用与 deadline 对齐，Mel 今日回应并宣布 v3
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 v3（移动 nr_cpus_allowed > 1 检查）发布后再评审
contribution_opportunities:
- kind: review
  description: 核对 v3 中检查组合顺序在 enqueue_task_rt/put_prev_task_rt 的一致性
- kind: testing
  description: PREEMPT_RT 构建下验证 migrate-disabled 任务不再触发无效 pull IPI
generated_at: '2026-11-14T01:30:00'
source_email_count: 1
related_articles:
- sched-20261111-002
- sched-20261112-009
tags:
- rt
- affinity
title: 'sched/rt: Do not account migrate-disabled tasks as pushable'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261111-002</a>：Mel Gorman 发三补丁修 RT 类 pushable 记账缺陷——migrate-disabled 任务仍被放进 pushable 列表并置起 `rq->rt.overloaded`，导致其它 CPU 的 pull IPI 反复命中「推不动」的任务、制造无效 IPI。刚发出时暂无回复。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-009-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261112-009</a>：Steven Rostedt 建议把 patch 2/3 折叠进 patch 1，Mel 同意折叠；v2 发出（单补丁）并 Peter Zijlstra 评审（问无条件保留 `is_migration_disabled()` 的副作用、请对 deadline 侧做同样处理）。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-017-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261113-017</a>（今天）：**Mel 回应 Peter**，解释会移动 `nr_cpus_allowed > 1` 检查、分析为何 deadline 侧不能简单照搬 `is_migration_disabled()`，并宣布 **v3 很快发出**。

## 背景与问题
（承接 20261111-002 / 20261112-009）`dae5c0292080` 修掉了 `pick_next_pushable_task()` 返回 migrate-disabled 任务的问题，但 `enqueue_task_rt()`/`put_prev_task_rt()` 仍把这些任务计为 pushable 并置起 `rq->rt.overloaded` 与 rto_mask，其它 CPU 每次 pull 触发的 IPI 可能只找到不可迁移任务。今日收口在检查成本与 deadline 侧是否对齐。

## 技术方案
今日为响应评审、无新代码（v3 预告）：
- 检查本身 `p->migration_disabled` 计算简单，但可能引入 cache miss（若此前无其它竞争者持自旋锁才 fetch 过该字段）；在 !PREEMPT_RT 上静态分支默认隐藏，属 PREEMPT_RT 特定风险。
- Mel 会移动 `nr_cpus_allowed > 1` 检查（回应 Peter 上一轮的追问）。
- deadline 侧**不能**加 `is_migration_disabled()`：deadline 没有 RT_PUSH_IPI 等价机制；加检查会伤害 `pull_dl_task`，且难察觉——如 rq 有多个更早 deadline 的可运行任务 + 1 个 migrate-disabled 任务时，两任务可能被留下竞争；有时加了又更好（早 deadline 但时间够跑完全的任务若与 migrate-disabled 任务同 rq 会被隐藏为 push 候选）。因此不追求 RT/DL 完全同步。

## 版本演进与当前进展
v1（三补丁）→ v2（单补丁，折叠后）→ **v3 很快发出**（移动 `nr_cpus_allowed > 1` 检查）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（上一轮）：问无条件保留 `is_migration_disabled()` 的副作用，请对 deadline 侧做同样处理。
- **Mel Gorman（作者）**：回应检查成本与 cache miss、deadline 侧不能照搬的理由，宣布 v3。
- 无 NAK；待发布 v3 后再评审。

## 合入评估
系列收敛为单补丁、维护者持续介入，合入概率高；当前卡在 v3 发布（移动 `nr_cpus_allowed > 1` 检查）。

## 效果评估
无今日新增 benchmark；此前结论为消除无效 pull IPI（承接 20261111-002）。

## 我可以参与的点
- **review**：核对 v3 中 `nr_cpus_allowed > 1` 与 `is_migration_disabled()` 检查的组合顺序在 `enqueue_task_rt()`/`put_prev_task_rt()` 两处是否一致。
- **testing**：在 PREEMPT_RT 构建下测 migrate-disabled 任务是否不再触发无效 pull IPI。

## 参考链接
- lore thread: https://lore.kernel.org/all/avXKCDm7NiVejDiF@techsingularity.net/
- Mel 今日回应: https://lore.kernel.org/all/avYpbK0s8vdbocyt@techsingularity.net/
