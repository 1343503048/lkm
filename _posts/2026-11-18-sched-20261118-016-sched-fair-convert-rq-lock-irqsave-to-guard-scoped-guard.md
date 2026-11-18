---
id: sched-20261118-016
date: '2026-11-18'
subject: 'sched/fair: Convert rq_lock_irqsave() to guard()/scoped_guard()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261118061712.14503-1-likunyu@open-hieco.net>
lore_url: https://lore.kernel.org/all/20261118061712.14503-1-likunyu@open-hieco.net/
authors:
- Li kunyu
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261118061712.14503-1-likunyu@open-hieco.net>
  date: '2026-11-18'
  summary: 三处 rq_lock_irqsave + 一处 rq_lock_irq 转 guard/scoped_guard
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 Peter/Vincent 收取
contribution_opportunities:
- kind: review
  description: 核对 sched_group_set_idle 的 goto next_cpu 转 continue 语义等价性
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- cfs
title: 'sched/fair: Convert rq_lock_irqsave() to guard()/scoped_guard()'
layout: article
---

## TL;DR

Li kunyu 发两补丁清理 `kernel/sched/fair.c` 的 rq 锁用法：把三处 `rq_lock_irqsave()/rq_unlock_irqrestore()` 对改成 `guard()/scoped_guard()`，把一处 `rq_lock_irq()/rq_unlock_irq()` 改成 `guard(rq_lock_irq)`，消除显式 `struct rq_flags` 局部变量。`sched_balance_rq()` 与 `__active_load_balance_cpu_stop()` 因其解锁路径与 IRQ 状态管理交错，刻意保持开放编码。纯清理，无行为变化，刚发出暂无回复。

## 背景与问题

内核已普及 `guard()`/`scoped_guard()` 的 scope-based 资源管理惯用法（配合 `DEFINE_GUARD` 的 `rq_lock_irqsave`/`rq_lock_irq` helper）。`fair.c` 里仍有多处手写的 `rq_lock_irqsave(rq, &rf) … rq_unlock_irqrestore(rq, &rf)` 对，需要显式 `struct rq_flags rf` 局部变量。作者把这些直截了当的配对转换为 guard 形式，使锁的作用域在代码结构上显式化。

## 技术方案

两补丁（2026-11-18 发出，无 cover）：

- **1/2 `Convert rq_lock_irqsave() to guard()/scoped_guard()`**（`kernel/sched/fair.c` +21/-28）：`_nohz_idle_balance()`、`__sched_group_set_shares()`、`sched_group_set_idle()` 三处改 `scoped_guard(rq_lock_irqsave, rq)`/`guard(rq_lock_irqsave)(rq)`。`sched_balance_rq()` 刻意保持开放编码——它在恢复 IRQ 前先释放 rq 锁，好让 `attach_tasks()` 在无 busiest rq 锁、但关中断下运行，scoped guard 会把两步折成单次 `unlock_irqrestore()` 而改变该语义。
- **2/2 `Convert rq_lock_irq() to guard()`**（`kernel/sched/fair.c` +1/-3）：`online_fair_sched_group()` 的 `rq_lock_irq()/rq_unlock_irq()` 改 `guard(rq_lock_irq)(rq)`；`__active_load_balance_cpu_stop()` 因解锁路径与 IRQ 状态管理交错，保持开放编码。

## 版本演进与当前进展

*current_version: v1（2026-11-18 发出，`<20261118061712.14503-1-likunyu@open-hieco.net>`，2 补丁）*。当日发出，无维护者回复。

## Maintainer 意见与讨论焦点

当日无维护者回帖。作者在补丁说明里对「哪些该转、哪些刻意不转」给了明确解释，属典型低争议清理。

## 合入评估

*likelihood=medium*。机械式清理、语义不变，历史同类 guard 转换争议极小；但无维护者表态，且涉及热路径锁函数。*blocking_issues*：无实质分歧，等待 maintainer review。*next_action*：等待 Peter/Vincent 收取。

## 效果评估

无运行时数据；纯清理，生成代码语义不变（显式 rq_flags 移交 guard 管理）。

## 我可以参与的点

- **review**：核对 `scoped_guard` 转换后 `sched_group_set_idle()` 里原 `goto next_cpu` 到 `continue` 的语义是否完全一致（原代码在 `WARN_ON_ONCE` 命中时 `goto next_cpu` 释放锁前还有后续逻辑）。

## 参考链接

- lore thread（1/2）: https://lore.kernel.org/all/20261118061712.14503-1-likunyu@open-hieco.net/
