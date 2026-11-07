---
id: sched-20261107-002
date: '2026-11-07'
subject: 'sched/deadline: bandwidth accounting fixes and selftests'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <20261107014451.1487825-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261107014451.1487825-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved: []
current_version: v4
patch_series:
- version: v2
  msgid: <20261104210445.2658802-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-05'
  summary: 21 补丁：17 修复 + 3 自测 + 1 sched_debug。
  review_outcome: Juri Reviewed-by/Acked-by，Marek Tested-by；Ingo 要求修复在前以便 stable 截取
- version: v3
  msgid: <20261105193359.1450487-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-06'
  summary: 24 补丁：20 修复 + sched_debug + 3 自测，吸收 Juri 4 个修复，新增 4 个修复。
  review_outcome: Kayra 复看 patch 1；sashiko AI 评审 9 补丁；无人类维护者回帖
- version: v4
  msgid: <20261107014451.1487825-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-07'
  summary: 26 补丁：22 修复 + sched_debug + 3 自测；新增 patch 21/22，崩溃修复提前到 patch 5/6。
  review_outcome: sashiko-bot 自动评审 9 补丁给出 15 条 medium/low；人类维护者未回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Juri 需对 patch 2/10/11/16 补回 Signed-off-by
  - sashiko 15 条 medium/low 发现待作者甄别
  - v4 刚发出，Ingo/Juri 尚未回复
  next_action: 等 Ingo/Juri 评审 v4；作者甄别 sashiko 发现；Juri 补 Signed-off-by
contribution_opportunities:
- kind: review
  description: 逐条甄别 sashiko 的 15 条 medium/low 发现是否属实并回帖
- kind: testing
  description: 复跑 Marek 的 CPU hotplug 测试与 52 用例自测，验证 cpusets 开关两种配置下的 rebuild 一致性
- kind: extend
  description: 核对 patch 21/22 边界是否还有未覆盖场景，可提交后续修复
generated_at: '2026-11-08T09:00:00+08:00'
source_email_count: 36
related_articles:
- sched-20261105-001
- sched-20261106-001
tags:
- deadline
- cgroup
title: 'sched/deadline: bandwidth accounting fixes and selftests'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了 CPU hotplug 崩溃并给 Tested-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a>：v3 发出，扩到 24 补丁——20 个修复（按 Ingo 要求修复在前，stable 可直接截取 1-20）+ patch 21 sched_debug + 3 个自测（52 用例），并把 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复全部吸收，新增 patch 5/7/13/16 四个新修复。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-002-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261107-002</a>（今天）：**v4 发出，扩到 26 补丁**——22 个修复 + patch 23 sched_debug + 3 个自测。相对 v3 新增两个修复（patch 21：replenishment timer 跨 class 往返残留、patch 22：boosted 任务设 SCHED_DEADLINE 后 this_bw 缺账 + sugov kthread 预留从不准入），并把「除零 active CPU」修复（现 patch 5）与 sysrq-n cpuset_mutex 修复（现 patch 6）表述更精确。作者明确 3 个 bug 可打死内核（patch 5/8/20）、2 个让 cpuset_mutex 不可用（1/6）。当日 sashiko-bot（AI 评审）对 9 个补丁给出 medium/low 级自动评审，无人类维护者回帖。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a> / 20261106-001）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除——第一个补丁在 Marek Szyprowski 的 CPU hotplug 测试上崩溃。Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，v4 继续按 Ingo 要求「修复在前，stable 可截取 1-22」，把 22 个 bug 按后果分四类：3 个直接打死内核（patch 5 除零 active CPU、patch 8 boosted owner 在 replenish_dl_entity 无限循环、patch 20 rebuild 记账撞上隔离 CPU 的 BUG()）；2 个让 cpuset_mutex 处于不可用状态（patch 1 二次解锁、patch 6 sysrq-n 在 tasklist_lock 下持锁）；3 个破坏预留保证（throttle 切出切回、0-lag 后沿用旧预留、replenishment timer 残留）；其余让 root domain 的 total_bw 或 runqueue 的 this_bw 与真实任务不符。

v4 相对 v3 的新增：patch 21（`Cancel the replenishment timer with the parameters`——replenishment timer 跨 class 往返后仍以「任务已离开的预留」的周期触发）、patch 22（`Count the bandwidth a boosted task is given`——boosted 任务设 SCHED_DEADLINE 后其 runqueue this_bw 缺账，sugov kthread 自己的预留从不准入）。patch 编号相对 v3 整体平移（v3 的 patch 5 现为 patch 7 等），因为 v4 把「除零 active CPU」与「sysrq-n」两个崩溃修复提前到 patch 5/6。sashiko-bot 的自动评审对 patch 4/8/9/10/14/15/16/20/26 给出 2+1 共约 15 条 medium/low 级发现（如「stale dl_bw_cpu 在 fallback 迁移后误记账」「dl_task_undepart() 丢 departed 状态」「__sched_setscheduler() 缺 dl_boosted 复位」等）。

## 技术方案

（承接 v2/v3 的「可追溯、可幂等」思路）v4 核心手段延续，关键点：

- **patch 1**：Andrea Parri 的 cpuset_mutex 二次解锁修复，原样携带（Waiman/Kayra/Juri 已评审），patch 6/14 依赖它。
- **patch 2/3**：`SCHED_FLAG_KEEP_PARAMS` 准入时序——拒绝会改 policy/class 的 KEEP_PARAMS（patch 2）、被保留参数不再无锁读取（patch 3）。
- **patch 5**：`__dl_sub()` 除零——CPU inactive 时拒绝 debugfs 写，而不是让写落到除法上。
- **patch 9/14/15/16/17/20**：root domain 记账的「记录」改造——记录记账 root domain 的 CPU（patch 16）、只在腾挪有空间时移动带宽、rebuild 从任务列表重建等。
- **patch 21（新）**：replenishment timer 跨 class 往返残留——参数变更时一并取消 timer。
- **patch 22（新）**：boosted 任务设 SCHED_DEADLINE 的 this_bw 记账 + sugov kthread 预留准入。
- **patch 23**：sched_debug 显示每 runqueue 的 deadline bandwidth；**patch 24-26**：三个自测（deadline_bw_test、deadline_rebuild_test、deadline_switch_test）。

系列基于 "locking/rtmutex: priority inheritance fixes and tests"（patch 8 依赖其 patch 3）。Juri 的 4 个修复仍由其本人补回 Signed-off-by。

## 版本演进与当前进展

*current_version: v4（2026-11-07 发出，msgid 20261107014451.1487825-1）*。

- v1（2026-11-03）：12 补丁。
- v2（2026-11-05）：21 补丁（17 修复 + 3 自测 + 1 sched_debug），获 Juri Reviewed-by/Acked-by、Marek Tested-by。
- v3（2026-11-06）：24 补丁（20 修复 + sched_debug + 3 自测），吸收 Juri 的 4 个修复，新增 4 个修复。
- v4（2026-11-07）：26 补丁（22 修复 + sched_debug + 3 自测），新增 patch 21/22，崩溃修复提前到 patch 5/6。当日 sashiko-bot 自动评审，人类维护者未回帖。

## Maintainer 意见与讨论焦点

当日无人类维护者回帖。cover 直陈与 Ingo/Juri 的既有往来：Ingo 要求「修复在前以便 stable 截取」，v4 已照做；Juri 的 4 个修复被 Ingo 从 sched/urgent 丢弃后，v4 全部吸收（patch 2/10/11/16），其中 patch 10/16 去掉了 Juri 的 Signed-off-by、留待 Juri 本人加回。sashiko-bot 的自动评审是当日唯一反馈来源，给出约 15 条 medium/low 级潜在问题（非人类、非最终裁定），作者此前亦披露 LLM 参与写作、请求熟悉该代码者仔细审阅修复本身。

## 合入评估

*likelihood=high*。系列四轮迭代、崩溃修复稳定-ready、按 Ingo 结构要求排列、Juri/Marek/Kayra/Waiman 均已审阅过早期版本。*blocking_issues*：① Juri 需对 patch 2/10/11/16 补回 Signed-off-by；② sashiko 的 15 条 medium/low 发现待作者甄别确认；③ v4 刚发出，Ingo/Juri 尚未回复。*next_action*：等 Ingo/Juri 评审 v4；作者甄别 sashiko 发现；Juri 补 Signed-off-by。

## 效果评估

本批无新性能数据（纯修复系列）。功能证据沿用早期：Marek Szyprowski 实测 v2 已修复其 CPU hotplug 崩溃板卡（cover 引「Marek found v2 fixed on the board that crashed」）。3 个可打死内核的 bug（patch 5/8/20）与 2 个 cpuset_mutex 不可用（patch 1/6）的修复，其收益是崩溃/死锁不复现，无量化指标。

## 我可以参与的点

- **review**：sashiko-bot 的 15 条 medium/low 发现（如「stale dl_bw_cpu 误记账」「dl_task_undepart() 丢 departed 状态」「__sched_setscheduler() 缺 dl_boosted 复位」）尚未有人类逐条甄别，值得对照代码核实真假并回帖——这正是作者在 cover 里明确请求的「熟悉该代码者仔细审阅」。
- **testing**：复跑 Marek 的 CPU hotplug 测试与新增的 52 用例自测，尤其在开启/关闭 cpusets 两种配置下验证 rebuild 记账一致性。
- **extend**：若核对发现 patch 21/22（timer 残留、boosted this_bw）还有边界未覆盖，可提交后续修复。

## 参考链接

- lore thread（v4 cover）: https://lore.kernel.org/all/20261107014451.1487825-1-mathieu.desnoyers@efficios.com/
- 依赖的 rtmutex 系列（cover 引用）: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
