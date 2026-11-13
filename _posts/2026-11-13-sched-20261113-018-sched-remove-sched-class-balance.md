---
id: sched-20261113-018
subject: 'sched: Remove sched_class::balance()'
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261107115913.261163891@infradead.org>
lore_url: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
authors:
- Peter Zijlstra
maintainers_involved:
- K Prateek Nayak
current_version: v2
patch_series:
- version: v2
  msgid: <20261107115913.261163891@infradead.org>
  date: 2026-11-07
  summary: 12 补丁重做 rq_clock/rq_lock 语义，12/12 移除 sched_class::balance()
  review_outcome: 暴露 rq->next_class 未提升问题；Peter 独立修复经 Kayra 实测通过
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者将 Fix wakeup_preempt() vs dl_server 并入系列并最终收取
contribution_opportunities:
- kind: testing
  description: core-sched/dl_server 环境跑调度 latency 回归
- kind: review
  description: 核对是否仍有未提升 rq->next_class 的入队路径
generated_at: '2026-11-14T01:30:00'
source_email_count: 1
related_articles:
- sched-20261107-001
- sched-20261108-005
- sched-20261109-007
- sched-20261111-005
- sched-20261112-011
tags:
- core_sched
- cfs
- deadline
- rt
title: 'sched: Remove sched_class::balance()'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-001-sched-core-sched-fixes-and-balancing.html">sched-20261107-001</a>：Peter Zijlstra 发 v2 系列（12 补丁）整体重做 rq_clock/rq_lock 语义；12/12 移掉 `sched_class::balance()` 后暴露 DL `rq->next_class` 未被 dl_server 路径提升的问题。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-011-sched-remove-sched-class-balance.html">sched-20261112-011</a>：Peter 给出 `sched/deadline: Fix wakeup_preempt() vs dl_server` 正式修复；Kayra 实跑发现其中 `dl_se->rq` 解引用崩溃，改成 `resched_curr(rq)` 后正常（latency 13us vs base 12us）；K Prateek 对「balance 是否必要 / RETRY_TASK 语义」提根本性疑问，Andrea Righi 从 sched_ext 角度确认分离 balance 与 pick 可行。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-018-sched-remove-sched-class-balance.html">sched-20261113-018</a>（今天）：**K Prateek Nayak 回复致谢**，修正自己此前「ops.acquire()/release() 仍是常态」的理解——`wakeup_preempt_scx()` → `scx_schedule_reenq_local()` 路径应能处理 balance_prev() 期间的高类 wakeup。当日无新补丁。

## 背景与问题
（承接 20261107-001 / 20261112-011）12/12 `Remove sched_class::balance()` 移除后暴露：`rq->next_class` 只被 `wakeup_preempt()` 提升，而 `dl_server_start()`/`dl_task_timer()`/`dl_server_timer()` 直接 `resched_curr()` 不经过它，导致 pick 失败后 balance 掉锁期间入队的 DL entity 无人注意、pick 不重启。此前 Peter 的修复被 Kayra 实测为坏修复，改由直接修 DL 侧。

## 技术方案
今日无新代码；K Prateek 收口此前对 sched_ext 侧「balance 与 pick 分离是否可行」的疑问——他原以为 `ops.acquire()`/`ops.release()` 仍是常态，经 Andrea/Peter 解释后确认 `wakeup_preempt_scx()` → `scx_schedule_reenq_local()` 路径足以在 `balance_prev()` 期间处理更高类的 wakeup。

## 版本演进与当前进展
v2 系列（12 补丁，20261107）→ 12/12 移 balance 暴露问题 → Peter 独立修复 `Fix wakeup_preempt() vs dl_server` → 今日无新版本，讨论收口。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak**：致谢并修正对 sched_ext acquire/release 常态的理解（接受 `scx_schedule_reenq_local()` 路径足以处理）。
- 无 NAK；此前 Peter 的 `sched/deadline: Fix wakeup_preempt() vs dl_server` 修复经 Kayra 实测通过（13us vs 12us）后待收取。

## 合入评估
系列接近收口，DL 侧修复已实测通过，合入概率高；当前主要待维护者把修复并入系列并最终收取。

## 效果评估
承接 20261112-011 实测：修复后 latency 13us vs base 12us（Kayra 实测，接近基线）。

## 我可以参与的点
- **testing**：在启用 core-sched / dl_server 的环境跑调度 latency 回归，确认 `Fix wakeup_preempt() vs dl_server` 无新增回退。
- **review**：核对 `rq->next_class` 是否仍有未提升的入队路径（除 dl_server timer 外）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261107115913.261163891@infradead.org/
- K Prateek 今日致谢: https://lore.kernel.org/all/5f0f320a-a718-4df8-922b-a3187861d6f8@amd.com/
