---
id: sched-20260917-003
date: '2026-09-17'
subject: 'sched_ext: Unlink pending local reenqueues before freeing scheduler'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: <20260916145807.3250167-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260916145807.3250167-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
- Cheng-Yang Chou
current_version: v1
patch_series:
- version: v1
  msgid: <20260916145807.3250167-1-arighi@nvidia.com>
  date: '2026-09-16'
  summary: 释放调度器前 unlink 挂起的 local reenqueue 请求
  review_outcome: Tejun 判定方向错误，被根因修复取代；Cheng-Yang Chou Acked
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 维护者认为 unlink 会掩盖丢失的调度，方向错误
  next_action: 被根因修复取代，无需继续推进
contribution_opportunities:
- kind: review
  description: 核对根因修复是否覆盖本补丁想防的 UAF 场景
generated_at: '2026-09-18T09:00:00'
source_email_count: 2
related_articles:
- sched-20260916-004
- sched-20260917-011
tags:
- sched_ext
title: 'sched_ext: Unlink pending local reenqueues before freeing scheduler'
layout: article
---

## TL;DR
增量更新：Andrea Righi 昨日（09-16）的"释放调度器前 unlink 挂起的 local reenqueue 请求"补丁被 Tejun Heo 判定为治标不治本——WARN 本就该触发、unlink 会掩盖下一处丢失的调度；根因已定位并用新补丁（Derive SCX_RQ_IN_WAKEUP，见 related）修复。Cheng-Yang Chou 补了一个 Acked-by。本补丁实质被取代。

## 背景与问题
背景见 sched-20260916-004：sched_ext 在释放调度器 per-cpu 区域时，一个仍挂链的 local reenqueue 请求会指向已释放区域，下一次调度器从 `run_deferred()` 解引用导致 UAF。Andrea 的原始补丁在释放前主动 unlink 挂起请求。

## 技术方案
无方案演进。Tejun 的回帖给出根因链：`move_remote_task_to_local_dsq()` 会把移动者的 enq_flags 暂存给目标 enqueue；自 57ccf5ccdc56 起这些 flags 决定 SCX_RQ_IN_WAKEUP；对一个忙碌远端 CPU 的 IMMED 插入会请求 local reenqueue，此时标志位被置位，`schedule_deferred_locked()` 把它留给 `task_woken_scx()`，但该路径下没人调用它——调度被丢失。正确修复是只测试 core enqueue flags 的 wakeup 位，即"Derive SCX_RQ_IN_WAKEUP"补丁。

## 版本演进与当前进展
- v1（09-16，`<20260916145807.3250167-1-arighi@nvidia.com>`）：原始 unlink 方案。
- 09-17：Tejun 判定该方案方向不对、另发根因修复；Cheng-Yang Chou 给出 Acked-by（"couldn't reproduce but lgtm"）。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：每条 link 后面都跟一次已调度的 `run_deferred()`，所以释放时仍挂链意味着那次 schedule 丢失；WARN 正是在做它的工作，unlink 只会掩盖下一个同类问题。根因在 move_remote_task_to_local_dsq 的 enq_flags 暂存，另帖修复。
- **Cheng-Yang Chou**：未能本地复现，但认可该修复思路（Acked-by）。
- 分歧点：unlink 的防御式修复被维护者否定，方向收敛到根因修复。

## 合入评估
*likelihood=rejected*。该补丁按原样不会被合并，被 Tejun 的根因修复（Derive SCX_RQ_IN_WAKEUP）取代。*blocking_issues*：维护者认为 unlink 掩盖真实问题、方向错误。*next_action*：无需继续推进本补丁，跟进根因修复的评审与合入。

## 效果评估
无性能数据；属正确性/UAF 类修复讨论。

## 我可以参与的点
- kind=review：核对根因修复（Derive SCX_RQ_IN_WAKEUP）是否覆盖本补丁想防的 UAF 场景，确认 IMMED 插入 + 忙碌远端 CPU 路径不再丢调度。

## 参考链接
- lore（v1）: https://lore.kernel.org/all/20260916145807.3250167-1-arighi@nvidia.com/
- Tejun 根因修复: https://lore.kernel.org/all/20260916215713.2701551-1-tj@kernel.org/
