---
id: sched-20260916-013
date: '2026-09-16'
subject: 'sched/cache: Introduce task_struct->sched_cache_grp'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <4532ec4fd5beb829bccb85822a19360fa4191fe6.1789061845.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/4532ec4fd5beb829bccb85822a19360fa4191fe6.1789061845.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved:
- Peter Zijlstra
current_version: null
patch_series:
- version: v1
  msgid: <4532ec4fd5beb829bccb85822a19360fa4191fe6.1789061845.git.tim.c.chen@linux.intel.com>
  date: '2026-09-15'
  summary: 在 task_struct 引入 sched_cache_grp 指针
  review_outcome: Peter 建议抽 rcu_deref_sched_cache_grp 助手宏、改用 rcu_dereference_protected
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - RCU 解引用写法需重构为助手宏
  next_action: 作者抽助手宏并重发
contribution_opportunities:
- kind: review
  description: 核对是否存在非 current 读路径需其它 RCU 原语
- kind: discussion
  description: 评估助手宏的放置位置
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles:
- sched-20260914-004
tags:
- cfs
title: 'sched/cache: Introduce task_struct->sched_cache_grp'
layout: article
---

## TL;DR
Tim Chen 的 cache-aware 系列 patch 4/4（本日为 Peter Zijlstra 评审轮）：在 `task_struct` 上引入 `sched_cache_grp` 指针。Peter 对 RCU 解引用写法提出意见——当下的 `rcu_dereference(...)` 带 `c`（update-side 校验）是反模式，建议抽一个 `rcu_deref_sched_cache_grp(tsk)` 助手宏（`rcu_dereference_protected(tsk->sched_cache_grp, tsk == current)`）以统一语义。合入可能性中等。

## 背景与问题
cache-aware 调度需要按任务记录其所属的 `sched_cache_group`。此前该指针挂在 mm 上（见 sched-20260916-012 的解耦），本 patch 在 `task_struct` 上直接引入 `sched_cache_grp` 字段，涉及对它的 RCU 解引用与更新侧校验。本 patch 的早期版本已在 sched-20260914-004 覆盖，这里是新一版评审。

## 技术方案
在 `task_struct` 引入 `sched_cache_grp` 指针。Peter 的评审集中在 RCU API 用法：更新侧用带 `c` 后缀的 `rcu_dereference` 是反模式（那个 `c` 是用来验证「确实是 update side、持有写锁」的），建议抽成助手宏避免到处重复，并考虑直接用 `rcu_dereference_protected()`（他本人更倾向无条件用 `rcu_dereference_*check()`；Alpha 上语义略有差异但已没人关心）。

## 版本演进与当前进展
- 本日为 Peter 对 4-patch 系列 patch 4/4 的评审（107225），聚焦 RCU 助手宏与 `rcu_dereference_protected()` 选择。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：①当前的「`c`」用法是反模式；②建议定义 `#define rcu_deref_sched_cache_grp(tsk) rcu_dereference_protected((tsk)->sched_cache_grp, (tsk) == current)`，避免重复；③考虑 `rcu_dereference_*check()` 的取舍。
- 无 NAK，意见可直接落实。

## 合入评估
*likelihood=medium*。意见明确且是 API 用法定型问题，Peter 参与积极，但尚需作者按建议修订并重发，且整个 4-patch 系列（1/3/4）都要过一遍评审。*blocking_issues*：RCU 解引用写法需按 Peter 建议重构成助手宏。*next_action*：作者抽助手宏并重发，协调 1/4 的 Fixes 标签。

## 效果评估
本日评审未涉及性能数据，属 RCU 用法与代码可维护性讨论。

## 我可以参与的点
- kind=review：核对 `sched_cache_grp` 的读侧（`tsk == current`）与写侧（持写锁）之间是否还存在非 current 读取路径需用其它 RCU 原语。
- kind=discussion：评估助手宏是放 sched.h 还是局部头文件更合适。

## 参考链接
- Peter 评审：https://lore.kernel.org/all/20260916130235.GG776954@noisy.programming.kicks-ass.net/
