---
id: sched-20260914-004
date: '2026-09-14'
subject: 'sched/cache: Introduce task_struct->sched_cache_grp'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <72bd9014ee83d5833bc1c78379ead84458045867.camel@linux.intel.com>
lore_url: https://lore.kernel.org/all/aqgF7JHKxQaE0W4b@chenyu-dev/
authors:
- Tim Chen
- Chen Yu
maintainers_involved:
- Chen Yu
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v2 重写（函数化 + rcu_dereference 修正）未发出
  - patch 3/4 与 4/4 打包合入互相绑定
  next_action: 等 v2 发出后核对 4/4 是否落实 PeterZ 两条批评
contribution_opportunities:
- kind: review
  description: v2 核对 rcu_dereference_protected(tsk->sched_cache_grp, tsk == current)
    与引用转移顺序
- kind: new_patch
  description: 回合自查：UAF 修复合入后比对内部分支 cache-aware 代码的引用生命周期
generated_at: '2026-09-15T09:30:00'
source_email_count: 1
related_articles:
- sched-20260911-003
tags:
- cfs
- load_balance
title: 'sched/cache: Introduce task_struct->sched_cache_grp'
layout: article
---

## TL;DR
增量更新，系列全貌见 sched-20260911-003（sched/cache: Fixes for cache aware scheduling 的 patch 4/4）。09-14 Chen Yu 回复 patch 4/4 的 rcu_dereference 用法修正方案：exec_mmap() 中 current 是唯一写者，改用 `rcu_dereference_protected(tsk->sched_cache_grp, tsk == current)`（仿 deref_curr_numa_group()）；未来支持 task tagging 出现多写者竞态时，再升级为 pi_lock 保护的 `rcu_dereference_protected(..., lockdep_is_held(&p->pi_lock))`（仿 prctl 系列做法）。这是对 PeterZ 批评「rcu_dereference_protected(true) 用法错误」的具体回应。

## 背景与问题
承 sched-20260911-003：patch 4/4 为 task_struct 增加 `__rcu` 的 `sched_cache_grp` 指针，任务在 copy_mm()/exec_mmap() 取自身引用、exit_mm() 释放。09-11 Peter Zijlstra 强烈批评实现风格（"This is horrific crap"），其中一条即 `rcu_dereference_protected(..., .condition = true)` 的用法错误；Tim Chen 承诺清理后发 v2。今日为 Chen Yu 对这条批评的具体修正口径。

## 技术方案
Chen Yu 的 rcu_dereference 修正（自述 "will fix it"）：

- 现状理解：exec_mmap() 中当前运行任务是 `tsk->sched_cache_grp` 的**唯一写者**，所以条件可写 `tsk == current`；
- 近期修正：`rcu_dereference_protected(tsk->sched_cache_grp, tsk == current);`，仿 `deref_curr_numa_group()`；
- 未来扩展：若支持 task tagging、出现多写者竞态，改用 `rcu_dereference_protected(tsk->sched_cache_grp, lockdep_is_held(&p->pi_lock));`，仿 prctl cache-aware 系列（lore 链接见参考）的做法。

## 版本演进与当前进展
- v1（09-11，见 sched-20260911-003）：patch 4/4 首发，被 PeterZ 打回。
- 09-14（本文窗口）：Chen Yu 给出 rcu_dereference 修正口径，v2 重写仍在进行、未发出。

## Maintainer 意见与讨论焦点
- **Chen Yu（作者方）**：给出 rcu_dereference 的具体修正口径并征询。
- **Peter Zijlstra**（承 09-11）：批评仍待 v2 验证——rcu_dereference 口径已定稿，但「函数化 exec/exit 路径」这条批评与整体 v2 重写尚未发出。
- 分歧/未闭合处：v2 的抽象程度（exec/exit 路径函数化到什么程度）仍待验证。

## 合入评估
*likelihood=medium*（承 sched-20260911-003 的整体判断）：rcu_dereference 口径已定稿，但 v2 未发、PeterZ 复核待。*blocking_issues*：v2 重写（函数化 + rcu_dereference 修正）未发出；patch 3/4 与 4/4 打包合入互相绑定（承 sched-20260911-003）。*next_action*：等 v2 发出后核对 4/4 是否落实 PeterZ 两条批评。

## 效果评估
无性能数据——UAF 修复的正确性工程（KASAN 实锤的 use-after-free，承 sched-20260911-003）。

## 我可以参与的点
- kind=review：v2 发出后核对 exec_mmap() 的 `rcu_dereference_protected(tsk->sched_cache_grp, tsk == current)` 与引用转移顺序（get 在 publish 前、put 在后）是否保持。
- kind=new_patch：回合自查——UAF 修复（sched_cache_group refcount + RCU free）若合入，需比对内部分支 cache-aware scheduling 代码路径的引用生命周期。

## 参考链接
- Chen Yu rcu_dereference 修正回帖：https://lore.kernel.org/all/aqgF7JHKxQaE0W4b@chenyu-dev/
- prctl cache-aware 系列（Chen Yu 引用）：https://lore.kernel.org/lkml/50fe2db1a62ea2376a87d0c14778b1ff456d11ec.1787955777.git.tim.c.chen@linux.intel.com/
