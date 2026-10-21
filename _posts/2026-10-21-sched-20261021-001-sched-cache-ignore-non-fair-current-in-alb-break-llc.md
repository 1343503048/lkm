---
id: sched-20261021-001
date: 2026-10-21
subject: 'sched/cache: Ignore non-fair current in alb_break_llc()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261020185402.57017-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20261020185402.57017-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20261020161755.55690-1-kayracizmeci@gmail.com>
  date: 2026-10-21
  summary: alb_break_llc() 中非 fair curr 置 NULL 后再取 util，避免喂给 task_misfits_asym_cpu()
  review_outcome: Tim Chen 确认 bug 实质是把非 fair curr 传给 task_misfits_asym_cpu()，要求补注释并改
    changelog
- version: v2
  msgid: <20261020185402.57017-1-kayracizmeci@gmail.com>
  date: 2026-10-21
  summary: 补注释 + changelog 指向 task_misfits_asym_cpu() 误用
  review_outcome: Tim Chen 给出 Reviewed-by，无分歧
upstream_commit: null
fixes_commit: f0d243a96f26
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 sched 维护者收取合入
contribution_opportunities: []
generated_at: '2026-10-22T01:30:00'
source_email_count: 5
related_articles: []
tags:
- cfs
- load_balance
title: 'sched/cache: Ignore non-fair current in alb_break_llc()'
layout: article
---

## TL;DR
Kayra Cizmeci 发往 sched 的单补丁修复：`alb_break_llc()` 里 commit `f0d243a96f26` 把 `rq->curr` 直接喂给 `task_misfits_asym_cpu()` 而不先判断其调度类，导致非 fair 任务（如 RT）的 curr 被当作 cache-aware 主动均衡判定依据——但主动均衡只会从 `cfs_tasks` 里 detach CFS 任务，非 fair curr 永不会被迁移，用它做判定是错的。v1 当日经 Tim Chen 两轮 review 后升 v2，Tim Chen 已给出 Reviewed-by。

## 背景与问题
`__active_load_balance_cpu_stop()` 通过 `detach_one_task()` 只从 `cfs_tasks` 列表挑选任务，故主动均衡只会迁移 CFS 任务。commit `d6b9afab44e23`（"sched/cache: Fix checking active load balance by only considering the CFS task"）已停止对非 fair 任务调 `task_util()`（非 fair 任务的 util 可能过期）；但后续 commit `f0d243a96f26`（"sched/fair: Avoid creating misfits during cache-aware balancing"）在 `alb_break_llc()` 里取 `cur = rq->curr` 后，只检查了 `cur->sched_class == &fair_sched_class` 才取 util，却仍把 `cur` 原样传给 `task_misfits_asym_cpu()`——该函数内部会对非 CFS 任务调 `task_fits_cpu()`。因为 `nr_pref_llc_running`/`h_nr_runnable` 只统计 CFS 任务，此时 `rq->curr` 可能是一个 RT 任务（其后队列里还有 CFS 任务），主动均衡却按它做 mismatch/LLC 判定，实属错误。

## 技术方案
单补丁（`kernel/sched/fair.c`，v2 为 +8/-1）：

- 在 `alb_break_llc()` 取 `cur` 后，若非 fair 类则把 `cur` 置 NULL：`if (cur && cur->sched_class != &fair_sched_class) cur = NULL;`
- 随后 `if (cur) util = task_util(cur);` 才对有效的 CFS curr 取 util，`task_misfits_asym_cpu()`/LLC 检查获得 NULL 后按要求跳过。
- v2 相较 v1：按 Tim Chen 建议补注释（"Active balance only detaches CFS tasks, so a non-fair curr is never migrated..."），并把 changelog 由「util 过期」改写为「问题在于把非 fair curr 喂给 `task_misfits_asym_cpu()`」这一更准确的表述。

## 版本演进与当前进展
*current_version: v2*。

- v1（`<20261020161755.55690-1-kayracizmeci@gmail.com>`）：初始修复，3 insertions / 1 deletion。
- v2（`<20261020185402.57017-1-kayracizmeci@gmail.com>`）：按 Tim Chen 意见补注释并重写 changelog 指向 `task_misfits_asym_cpu()` 误用；作者注明该版未 compile-test（仅改注释）。

## Maintainer 意见与讨论焦点
Tim Chen（Intel cache-aware 工作核心作者）两轮反馈均为认可+打磨：第一轮确认「util 本来就对非 fair curr 是 0，真正的 bug 是把 cur 传给 `task_misfits_asym_cpu()`」，要求补注释并改 changelog；随后又建议把 changelog 重写为说明 `f0d243a96f26`「仍把 curr 传给 `task_misfits_asym_cpu()` 而不论其类」。Tim Chen 最终给出 *Reviewed-by*，无分歧。

## 合入评估
*likelihood=high*。修复直指已合入的 `f0d243a96f26` 回归、带 `Fixes:`，方向无异议且已获领域核心开发者 Reviewed-by。*blocking_issues*：无实质阻塞。*next_action*：等 sched 维护者（Peter Zijlstra / Vincent Guittot）收取即可。

## 效果评估
无 benchmark 数据。属正确性修复：消除把非 fair curr 误用于主动均衡 mismatch/LLC 判定的隐患（涉及 RT 任务与 CFS 任务混在 rq 上的 cache-aware 场景）。

## 我可以参与的点
当前阶段已由核心开发者 review 通过，暂无明显参与空间，可持续观察其是否进入 tip 分支。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261020185402.57017-1-kayracizmeci@gmail.com/
- v1 patch：https://lore.kernel.org/all/20261020161755.55690-1-kayracizmeci@gmail.com/
- Tim Chen 最终 Reviewed-by：https://lore.kernel.org/all/96c89ebc2cd7f8217e0053a7e5302594fb039683.camel@linux.intel.com/
