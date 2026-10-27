---
id: sched-20261027-002
date: 2026-10-27
subject: 'sched_ext: Fix the stall watchdog testing and blaming the wrong sched under
  bypass'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261026204300.3618150-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261026204300.3618150-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261026204300.3618150-1-tj@kernel.org>
  date: 2026-10-27
  summary: watchdog 改测实际运行任务的 sched 的 timeout；bypass requeue 重启 wait
  review_outcome: Andrea Reviewed-by，当日合入 for-7.4-fixes
upstream_commit: null
fixes_commit: 2c91169377f4
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 for-7.4-fixes，等待随 sched_ext pull 进主线
contribution_opportunities: []
generated_at: '2026-10-28T09:00:00'
source_email_count: 3
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix the stall watchdog testing and blaming the wrong sched under
  bypass'
layout: article
---

## TL;DR
Tejun Heo 发往 sched_ext/for-7.4-fixes 的单补丁修复：bypassing 调度器的任务由其 host（最近的非 bypassing 祖先）运行，而 stall watchdog 在 `check_rq_for_timeouts()` 里对 task 测的是「owner 的 timeout」、eject 的却是「DSQ 所属调度器」，三者（被测 sched、被 eject sched、运行任务的 sched）可能各不相同，导致误责甚至整个 sched_ext 被 disable。补丁统一改测「实际运行该任务的 sched」的 timeout 并 blame 之；已在 10-27 当天合入 sched_ext/for-7.4-fixes。

## 背景与问题
commit `2c91169377f4`（"sched_ext: Blame the DSQ's owning scheduler for a runnable stall"）让 stall watchdog 把卡在 DSQ 上的任务 blame 给 DSQ 所属调度器。但 bypass 下这一归责是错的：timeout 是 per-sched 的，bypassing 子调度器（如 2s timeout）的任务落在 root（默认 30s）的 bypass DSQ 上，任务等满 2s 就会 eject root、把整个 sched_ext 禁用；bypassing owner 的任务也可能被 blame 给「什么都不放置」的 owner，若 owner 正在 exit 则 exit 变 no-op、任务永远不被 eject。此外 bypass 移动任务时 wait 不重启，等待时长会跨 sched 错算。

## 技术方案
运行时判定「谁在实际运行该任务」：owner 运行，或 owner bypassing 时由 host 运行。watchdog 改测该 sched 的 timeout 并 blame 它（`scx_exec_sched()` 语义）；`scx_bypass()` 的 requeue 可能改变运行任务的 sched，故对每个被 requeue 的任务除 root 自身外重启 wait（新 `SCX_TASK_RESET_RUNNABLE_AT` 标志）。单调度器行为不变。`Fixes: 2c91169377f4`，`Cc: stable`（v7.3+）。

## 版本演进与当前进展
*current_version: v1*。该补丁是 v3 bypass 系列 19/17（"Fix the stall watchdog blaming a bypassing owner for a stuck task"）拆分后独立发出的版本，10-27 当天直接合入 for-7.4-fixes。

## Maintainer 意见与讨论焦点
Andrea Righi 给 `Reviewed-by`；Tejun Heo 作为 sched_ext 维护者当日 `Applied to sched_ext/for-7.4-fixes`。无争议。

## 合入评估
*likelihood=merged*。已合入 sched_ext/for-7.4-fixes（*merged_branch=sched_ext/for-7.4-fixes*）。

## 效果评估
正确性修复，未附定量性能数据。cover 注明「迁移与 requeue 竞态」的 rare race 未在本版解决（任务恰在 scx_bypass 遍历中迁移时 wait 会保留并记到新 sched），作者判断现实影响有限、留作未来。

## 我可以参与的点
当前阶段已合入，暂无明显参与空间；可关注 rare race（bypass 遍历中迁移）若成为现实问题再跟进。

## 参考链接
- patch: https://lore.kernel.org/all/20261026204300.3618150-1-tj@kernel.org/
