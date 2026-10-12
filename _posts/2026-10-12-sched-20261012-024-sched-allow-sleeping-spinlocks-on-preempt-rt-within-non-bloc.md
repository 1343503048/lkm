---
id: sched-20261012-024
date: '2026-10-12'
subject: 'sched: Allow sleeping spinlocks on PREEMPT_RT within non_block_start()/end
  block.'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261012101704.gZyF2O9M@linutronix.de>
lore_url: https://lore.kernel.org/all/20261012101704.gZyF2O9M@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- David Woodhouse
current_version: v3
patch_series:
- version: v2
  msgid: <20260916155105.qDi2MiYW@linutronix.de>
  date: '2026-09-16'
  summary: 给 __might_resched() 增加 sleeping_lock 参数区分正常调度与 sleeping lock
  review_outcome: David Woodhouse Acked-by
- version: v3
  msgid: <20261012101704.gZyF2O9M@linutronix.de>
  date: '2026-10-12'
  summary: Repost 收集 tags；rtlock_might_resched 传 true
  review_outcome: 当日新发，David Acked-by 仍在
fixes_commit: 312364f3534c
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 跨 mm/locking 边界改动，需 Peter/Rafael 等收取
  next_action: 等维护者收取（David Woodhouse 已 Acked）
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 1
related_articles:
- sched-20260821-002
- sched-20260916-019
tags:
- preempt
- rt
title: 'sched: Allow sleeping spinlocks on PREEMPT_RT within non_block_start()/end
  block.'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/08/21/sched-20260821-002-sched-allow-sleeping-spinlocks-on-preempt-rt-within-non-block.html">sched-20260821-002</a> / 20260916-019：Sebastian Siewior 修 PREEMPT_RT 下 `non_block_start()/end()` 区间内获取 sleeping spinlock 触发 might_sleep splat 的问题——给 `__might_resched()` 加 `sleeping_lock` 参数区分「来自可睡眠锁的调度请求」；David Woodhouse 已 Acked。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-024-sched-allow-sleeping-spinlocks-on-preempt-rt-within-non-bloc.html">sched-20261012-024</a>（今天）：作者发 v3（Repost 收集 tags），把 `rtlock_might_resched()` 的调用改为传 `true`（可睡眠锁），并给 `cond_resched*` 系列传 `false`；`Fixes: 312364f3534c` + syzbot Reported-by。

## 背景与问题

（承接 20260821-002/20260916-019）`non_block_start()/end()` 为捕捉依赖锁/可睡眠条件的回调而引入，当初把 spinlock 排除在外；但 PREEMPT_RT 上 `spinlock_t`/`rwlock_t` 是可睡眠自旋锁（带 `might_sleep()`），锁竞争时 `schedule()`，于是在 non_block 块内触发 splat。

## 技术方案

（承接 20260916-019）v3 保持 v2 思路：`__might_resched()` 增 `bool rt_sleeping_lock` 参数；`rtlock_might_resched()`（PREEMPT_RT 两种 sleeping lock 都用）传 `true`，其余 `cond_resched*`/`__might_sleep` 传 `false`；判定条件里 `(rt_sleeping_lock || !current->non_block_count)` 让 sleeping-lock 的调度请求不因 non_block_count 而告警。

## 版本演进与当前进展

- v1（08-21）→ v2（09-16，加 syzbot Reported-by）→ v3（10-12，Repost 收集 tags）。
- David Woodhouse 的 `Acked-by` 保留至今。

## Maintainer 意见与讨论焦点

无分歧；David Woodhouse（non_block 引入者）已 Acked-by。跨 `include/linux/kernel.h`、`sched.h`、`spinlock_rt.c`、`core.c` 四文件。

## 合入评估

*likelihood=medium*。逻辑清晰、有 Acked-by，但横跨 mm/locking 边界需相应维护者收取。*blocking_issues*：等待收取。*next_action*：等维护者合入。

## 效果评估

无性能数字（RT splat 修复，未见 benchmark）。

## 我可以参与的点

改动已稳定且 Acked，当前阶段暂无明显参与空间。

## 参考链接

- lore（v3）: https://lore.kernel.org/all/20261012101704.gZyF2O9M@linutronix.de/
