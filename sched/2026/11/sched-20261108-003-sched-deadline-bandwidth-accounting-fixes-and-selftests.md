# sched/deadline: bandwidth accounting fixes and selftests

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-001：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（其中 3 个可直接打死内核），带自测与 sched_debug。Juri 已对多数补丁给 Reviewed-by/Acked-by，Marek Szyprowski 实测修复了 CPU hotplug 崩溃并给 Tested-by；Ingo 要求「严格只含 -stable 可回退修复的子集」。
- sched-20261106-001：v3 发出，扩到 24 补丁——20 个修复（按 Ingo 要求修复在前，stable 可直接截取 1-20）+ patch 21 sched_debug + 3 个自测（52 用例），并把 Juri 被 Ingo 丢弃的 4 个 sched/urgent 修复全部吸收，新增 patch 5/7/13/16 四个新修复。
- sched-20261107-002：v4 发出，扩到 26 补丁——22 个修复 + patch 23 sched_debug + 3 个自测。相对 v3 新增两个修复（patch 21：replenishment timer 跨 class 往返残留、patch 22：boosted 任务设 SCHED_DEADLINE 后 this_bw 缺账 + sugov kthread 预留从不准入），并把「除零 active CPU」修复（现 patch 5）与 sysrq-n cpuset_mutex 修复（现 patch 6）表述更精确。当日 sashiko-bot（AI 评审）对 9 个补丁给出 medium/low 级自动评审，无人类维护者回帖。
- sched-20261108-003（今天）：**作者逐条回应 sashiko-bot 对 9 个补丁（4/8/9/10/14/15/16/20/26）的评审发现**，多数为「Right，确认属实」并给出机理解释，少数点明「这超出本系列范围」。回应中密集披露 v5 计划：新增「deboost 结束时重置 deadline/runtime」与「任务被迫离开 CPU 时搬运带宽与记录」两个补丁、patch 15 后移到 patch 16 之后、给 patch 14 的 task-list 遍历补 dl_bw_gen 检查、若干自测用例扩展。仍无人类维护者回帖。

## 背景与问题

（承接 sched-20261105-001 / 20261106-001 / 20261107-002）Juri Lelli 前一轮 4 个 SCHED_DEADLINE 带宽记账修复被 Ingo 从 tip/sched/urgent 移除（首个补丁在 Marek 的 CPU hotplug 测试上崩溃），Mathieu Desnoyers 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷，按 Ingo 要求「修复在前、stable 可截取」推进到 v4（26 补丁：22 修复 + sched_debug + 3 自测）。3 个 bug 可打死内核（patch 5/8/20），2 个让 cpuset_mutex 不可用（patch 1/6），其余让 root domain 的 total_bw 或 runqueue 的 this_bw 与真实任务不符。

今日新进展是作者对 sashiko-bot 自动评审的逐条澄清：这些 medium/low 发现集中在「boosted 任务的带宽何时/如何释放与重建」这类 dl_bw 生命周期边界。作者在回应中确认了大部分边界确实需要收尾（并预告 v5 落地），同时驳回个别超出系列范围的点（如 patch 10 的 0-lag 时间跨 boost 保留）。

## 技术方案

（承接 v2/v3/v4 的「可追溯、可幂等」记账思路）今日无新版本补丁，为 v5 计划的技术方向披露：

- **patch 4（boosted 任务改 policy）**：确认修复前调用 `EBUSY` 失败、现在 sysrq-n 可把 boosted 任务移出 class；v5 在 `__setscheduler_dl_pi()` 里当新优先级非 deadline 时清除 boost。作者解释 boosted 任务本就不受 throttle（`update_curr_dl_se()` 即时补、`enqueue_task_dl()` 解除 throttle），故此前调用对运行无额外影响。
- **patch 8/9（deadline boost 来源与参数复位）**：patch 8 的 sysrq-n 是 patch 4 同款 bug，v5 的 patch 4 修复会在此清 `dl_boosted`。patch 9 明确 deboost 时 `task_non_contending()` 仅在 0-lag 时间在前时保留 runtime，否则带宽随参数一并释放；v5 新增补丁在「boost 结束时 runtime 高于任务自身」时重置 deadline/runtime，并加自测用例。
- **patch 10（sleep 离开 class 释放带宽）**：确认释放路径唯一，且作者主动把「0-lag 时间跨 boost 保留」排除出本系列（会改变 inactive timer 对 boosted 任务的处理）。
- **patch 14/15/16（root domain 记账重建）**：task-list 遍历能发现 cpuset 遍历漏掉的 unreaped zombie；v5 给遍历补 `dl_clear_root_domains()` 的 `dl_bw_gen` 检查、把 patch 15 后移到「Record the root domain holding a task's bandwidth」（现 patch 16）之后，并在注释里写明 deboost 竞态。
- **patch 20（rebuild 记到任务所在 CPU）**：v5 优先取任务当前所在 CPU（若 active 且在任务 mask 内），新增补丁在任务被 `select_fallback_rq()` 放到别的 root domain 时搬运带宽与记录，自测用 `isolcpus=domain` 跑。
- **patch 26（自测）**：v5 让两个用例都等到 owner 以 waiter 优先级运行，超时未等即判失败。

系列仍基于 "locking/rtmutex: priority inheritance fixes and tests"（patch 8 依赖其 patch 3）。

## 版本演进与当前进展

*current_version: v4（2026-11-07 发出，msgid 20261107014451.1487825-1）*。今日为作者对 sashiko-bot 评审的逐条回应，v5 正在筹备中（作者回应里多次「v5 will / v5 adds / v5 moves」）。

- v1（2026-11-03）：12 补丁。
- v2（2026-11-05）：21 补丁，获 Juri Reviewed-by/Acked-by、Marek Tested-by。
- v3（2026-11-06）：24 补丁，吸收 Juri 的 4 个修复，新增 4 个修复。
- v4（2026-11-07）：26 补丁，新增 patch 21/22，崩溃修复提前到 patch 5/6；sashiko-bot 自动评审。
- v5（筹备中，未发出）：新增 deboost 参数复位与 fallback 搬运两个补丁、patch 15 后移、dl_bw_gen 检查、自测扩展。

## Maintainer 意见与讨论焦点

当日仍无人类维护者回帖。今日全部反馈来自作者对 sashiko-bot（AI 评审）9 条发现的自查式回应，口径以「Right，确认」为主，仅 patch 10 明确表示「I would leave that out of this series」。与人类维护者的既有往来不变：Ingo 要求修复在前以便 stable 截取、Juri 需对 patch 2/10/11/16 补回 Signed-off-by，均无更新。

## 合入评估

*likelihood=high*。系列四轮迭代、崩溃修复稳定-ready、按 Ingo 结构要求排列，今日作者又主动回应了 sashiko 的全部发现并预告 v5 收尾，显示作者在积极收敛。*blocking_issues*：① Juri 需对 patch 2/10/11/16 补回 Signed-off-by；② v5 尚未发出，当前 sashiko 发现要靠 v5 落地才算闭环；③ Ingo/Juri 仍无回复。*next_action*：作者发 v5（落地上述边界修复）后，等 Ingo/Juri 评审并补 Signed-off-by。

## 效果评估

本批为评审讨论，无新量化数据（纯修复系列）。功能证据沿用：Marek Szyprowski 实测 v2 已修复其 CPU hotplug 崩溃板卡；3 个可打死内核的 bug 与 2 个 cpuset_mutex 不可用的修复，收益是崩溃/死锁不复现，无量化指标。

## 我可以参与的点

- **review**：作者对 sashiko 9 条发现的回应中有几处「Right，但 v5 才改」，可在 v5 发出后对照代码核实这些边界（deboost 参数复位、fallback 搬运、task-list 遍历的 dl_bw_gen）是否真正闭合。
- **testing**：复跑 Marek 的 CPU hotplug 测试与自测，尤其在开启/关闭 cpusets 两种配置下验证 rebuild 记账一致性，重点覆盖 v5 新增的 `isolcpus=domain` 用例。
- **extend**：patch 10 被作者排除的「0-lag 时间跨 boost 保留」若后续成为真实边界缺陷，可独立提交。

## 参考链接

- lore thread（v4 cover）: https://lore.kernel.org/all/20261107014451.1487825-1-mathieu.desnoyers@efficios.com/
- 今日作者回应（patch 26 一例）: https://lore.kernel.org/all/0f916c89-c184-429f-93a1-0f5b28e516b8@efficios.com/
- 依赖的 rtmutex 系列（cover 引用）: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20261108-003
date: '2026-11-08'
subject: "sched/deadline: bandwidth accounting fixes and selftests"
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: "<20261107014451.1487825-1-mathieu.desnoyers@efficios.com>"
lore_url: "https://lore.kernel.org/all/20261107014451.1487825-1-mathieu.desnoyers@efficios.com/"
authors: ["Mathieu Desnoyers"]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: "<20261107014451.1487825-1-mathieu.desnoyers@efficios.com>"
    date: '2026-11-07'
    summary: "26 补丁：22 修复 + sched_debug + 3 自测；新增 patch 21/22，崩溃修复提前到 patch 5/6。"
    review_outcome: "sashiko-bot 自动评审 9 补丁；作者今日逐条回应并预告 v5"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "Juri 需对 patch 2/10/11/16 补回 Signed-off-by"
    - "v5 尚未发出，sashiko 发现需 v5 落地闭环"
    - "Ingo/Juri 仍无回复"
  next_action: "作者发 v5 落地边界修复，等 Ingo/Juri 评审并补 Signed-off-by"
contribution_opportunities:
  - kind: review
    description: "v5 发出后核实 deboost 参数复位、fallback 搬运、dl_bw_gen 检查等边界是否闭合"
  - kind: testing
    description: "复跑 Marek 的 CPU hotplug 测试与自测，覆盖 v5 新增的 isolcpus=domain 用例"
  - kind: extend
    description: "patch 10 被排除的 0-lag 时间跨 boost 保留若成真实缺陷可独立提交"
generated_at: "2026-11-09T09:00:00+08:00"
source_email_count: 9
related_articles: [sched-20261105-001, sched-20261106-001, sched-20261107-002]
tags: [deadline, cgroup]
---