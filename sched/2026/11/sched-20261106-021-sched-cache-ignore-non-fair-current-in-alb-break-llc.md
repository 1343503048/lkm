# sched/cache: Ignore non-fair current in alb_break_llc()

## TL;DR

Kayra Cizmeci 的 cache-aware 调度修复（此前 10 月发出并获 Tim Chen Reviewed-by）今日被 Ingo Molnar 合入 tip/sched/urgent：`alb_break_llc()` 会把非 fair 的 `rq->curr` 原样喂给 `task_misfits_asym_cpu()`，而主动均衡只会从 `cfs_tasks` detach CFS 任务、非 fair curr 永不会被迁移——用它做 misfit/LLC 判定是错的。合入 commit `006991aa89974378ee579416dba87adc22cd60fd`。

## 背景与问题

`__active_load_balance_cpu_stop()` 通过 `detach_one_task()` 只从 `cfs_tasks` 列表挑任务，故主动均衡只迁移 CFS 任务。commit `f0d243a96f26`（"sched/fair: Avoid creating misfits during cache-aware balancing"）在 `alb_break_llc()` 里取 `cur = rq->curr` 后只对 fair 类才取 util，却仍把 `cur` 原样传给 `task_misfits_asym_cpu()`——当 `rq->curr` 是 RT 任务（后面队列里还有 CFS 任务）时，主动均衡按它做 mismatch/LLC 判定，实属错误。

## 技术方案

在 `alb_break_llc()` 里把非 fair 的 curr 置为 NULL（`if (cur && cur->sched_class != &fair_sched_class) cur = NULL;`），避免其状态 util 进入 misfit 与 LLC 判定。改动 `kernel/sched/fair.c` +8/-1 行。

## 版本演进与当前进展

*current_version: v2（2026-10-20 发出）*。10 月经 Tim Chen 两轮 review 升 v2 并获 Reviewed-by；今日（11-06）Ingo 合入 tip/sched/urgent。

## Maintainer 意见与讨论焦点

Tim Chen 已给 Reviewed-by；Peter Zijlstra 与 Ingo Molnar 连带 Signed-off-by，方向无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent（`merged_branch=tip/sched/urgent`），commit `006991aa89974378ee579416dba87adc22cd60fd`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线。

## 效果评估

无量化性能数据（语义修复：避免非 fair curr 污染 cache-aware 主动均衡判定）。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/006991aa89974378ee579416dba87adc22cd60fd
- 原补丁 lore: https://patch.msgid.link/20261020185402.57017-1-kayracizmeci@gmail.com

---
id: sched-20261106-021
date: 2026-11-06
subject: "sched/cache: Ignore non-fair current in alb_break_llc()"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<179395863356.1009794.10322114886183761945.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179395863356.1009794.10322114886183761945.tip-bot2@tip-bot2/"
authors: [Kayra Cizmeci]
maintainers_involved: [Ingo Molnar, Peter Zijlstra]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261020185402.57017-1-kayracizmeci@gmail.com>"
    date: 2026-10-20
    summary: "alb_break_llc 对非 fair curr 置 NULL，避免 misfit/LLC 误判。"
    review_outcome: "Tim Chen Reviewed-by；11-06 合入 tip/sched/urgent。"
upstream_commit: "006991aa89974378ee579416dba87adc22cd60fd"
fixes_commit: "f0d243a96f26"
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/urgent 进入主线"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261021-001]
tags: [cfs, load_balance]
---