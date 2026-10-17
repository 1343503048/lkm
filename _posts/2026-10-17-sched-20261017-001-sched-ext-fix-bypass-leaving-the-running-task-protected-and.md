---
id: sched-20261017-001
subject: 'sched_ext: Fix bypass leaving the running task protected and bypassed tasks
  stranded'
date: 2026-10-17
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261017053717.3162619-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261017053717.3162619-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261017053717.3162619-1-tj@kernel.org>
  date: 2026-10-17
  summary: 2 补丁：运行任务保护剥离移到遍历外 + caps 按运行它的调度器检查并在 bypass 解除时逐出
  review_outcome: Andrea Righi Reviewed-by，两点备注被 Tejun 确认；当日 applied
upstream_commit: null
fixes_commit: 9cfc6ab34a31
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 for-7.3-fixes 合并主线；for-7.4 合并时 strip/evict 改用 rq->donor
contribution_opportunities: []
generated_at: '2026-10-18T01:10:00'
source_email_count: 6
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix bypass leaving the running task protected and bypassed tasks
  stranded'
layout: article
---

## TL;DR
Tejun Heo 发往 `sched_ext/for-7.3-fixes` 的 2 补丁修复系列：`scx_bypass()` 在遍历 runnable 列表时处理运行中任务，但运行中任务根本不在该列表上，导致 bypass 进入时的保护剥离永不执行、受保护运行任务的 slice 在 bypass 里切不动；另一方面，被 bypass 的子调度器任务由最近非 bypass 祖先运行，但其能否停留仍按任务自身调度器的 caps 检查，被 bypass 负载均衡搬到「自身调度器无 caps 的 CPU」的任务 slice 耗尽后无法停留、CPU 可能带着排队任务 idle。当日已被 Tejun applied 到 `sched_ext/for-7.3-fixes`。

## 背景与问题
两个独立缺陷：
1. `scx_bypass()` 对运行中任务的处理写在了对 `rq->scx.runnable_list` 的遍历之内——但运行中任务从不在这条列表上（`set_next_task_scx()` 摘下、`put_prev_task_scx()` 放回），因此「bypass 进入时剥离运行任务保护」的代码从未执行。一个受保护（`SCX_TASK_PROTECTED`）的运行任务会把 slice 带进 bypass，bypass tick 对它切 slice 的尝试被拒绝。
2. 被 bypass 的子调度器任务由其最近非 bypass 祖先运行，祖先把它放到自己的本地 DSQ、按自身 caps 处理；但「该任务能否停留此 CPU」「cap 撤销后是否 reenqueue」仍按任务**自身**调度器的 caps 判断。bypass 负载均衡搬运任务时不看 caps，于是被 bypass 任务可能运行在自身调度器无 caps 的 CPU 上——slice 一旦耗尽就无法停留，任务进入祖先的 bypass DSQ 却没有 kick，CPU 可能带着排队任务 idle 直到别处重新调度该 CPU。

## 技术方案
两个补丁（`kernel/sched/ext/{ext.c,internal.h,sub.c,sub.h}`，+46/−16）：
- **Patch 1/2**：把「剥离运行任务保护」挪到遍历之外、在 bypass 置位时对 `rq->curr` 显式执行 `scx_task_slice_ended()`。
- **Patch 2/2**：新增 `scx_exec_sched()` 辅助函数（沿 `scx_parent()` 链找到实际运行该任务调度器的最近非 bypass 祖先），把 caps 检查（`scx_task_can_stay_on_cpu()`/`scx_task_reenq_on_cap_revoke()`）从「任务自身调度器」改为「运行它的调度器」；并在 bypass 解除时，若运行任务无法停留该 CPU 则 `scx_set_task_slice(p, 0)` 逐出。附带移除 `bypass_enq_target_dsq()` 中 `CONFIG_EXT_SUB_SCHED` 下重复的祖先查找逻辑，统一走 `scx_exec_sched()`。
- `Fixes:` 分别指向 `9cfc6ab34a31`（Add SCX_TASK_PROTECTED）、`75a8c8202c91`（reject DSQ）、`46a85ae6fe5b`（cpu occupancy 挂到 SCX_CAP_BASE）。

## 版本演进与当前进展
v1 首版（2 补丁，cover `<20261017053717.3162619-1-tj@kernel.org>`），当日发出并被 applied，无更早版本记录。

## Maintainer 意见与讨论焦点
Andrea Righi 给出 Reviewed-by，并附两点：
1. 合并进 `for-7.4` 时（有 proxy exec）slice 与保护归属 donor，strip 与 evict 均应使用 `rq->donor` 而非 `rq->curr`；Tejun 回复确认合并到 for-7.4 时两处都会改用 `rq->donor`。
2. 非回归、可能只是过渡现象（未验证）：`bypass_lb_cpu()` 不看 caps，当运行被 bypass 任务的最近非 bypass 祖先自身也是「只在部分 CPU 上有 caps」的子调度器时，被 bypass 任务是否仍可能被搬到无法停留的 CPU、直到 bypass 解除？Tejun 回复此事已在另一个独立系列中处理。

## 合入评估
*likelihood=merged*。Tejun 已明确「Applied 1-2 to sched_ext/for-7.3-fixes」，进入维护者修复分支，待后续合并主线。*blocking_issues*：无。*next_action*：随 for-7.3-fixes 合并主线；for-7.4 合并时改用 rq->donor（已在计划内）。

## 效果评估
作者验证（cover 原文）：裸机上带负载反复 attach/detach 子调度器，一个在每个 bypass 入口把运行任务标记为 protected 的 debug knob 在补丁 1 下发现每个此类任务都被剥离；无补丁时它们全部保留保护、bypass tick 切不动 slice。VM 中，自身调度器无 caps 的运行任务在补丁 2 下于 bypass 解除后约 50µs 内离开该 CPU，而不是跑完整个 bypass slice。sched_ext selftests 全部通过。

## 我可以参与的点
系列已合入 `sched_ext/for-7.3-fixes`，当前阶段暂无明显参与空间；可关注 for-7.4 合并时 proxy exec 下 `rq->donor` 化改动，以及 Tejun 提到的「bypass_lb_cpu() 不看 caps」独立系列的后续。

## 参考链接
- patchset cover：https://lore.kernel.org/all/20261017053717.3162619-1-tj@kernel.org/
- patch 1/2：https://lore.kernel.org/all/20261017053717.3162619-2-tj@kernel.org/
- patch 2/2：https://lore.kernel.org/all/20261017053717.3162619-3-tj@kernel.org/
- Andrea Righi 的 review：https://lore.kernel.org/all/atNKHI9K-_Rbh9Og@gpd4/
- Tejun 的 applied 回帖：https://lore.kernel.org/all/74cb2c89df23fe72711e7018655c589b@kernel.org/
- 未获取到 tip-bot commit（尚无主线 commit）。
