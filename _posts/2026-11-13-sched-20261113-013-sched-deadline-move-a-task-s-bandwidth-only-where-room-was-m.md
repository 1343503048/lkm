---
id: sched-20261113-013
subject: 'sched/deadline: Move a task''s bandwidth only where room was made'
date: 2026-11-13
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20261108185406.1549770-19-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261108185406.1549770-19-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
- Waiman Long
current_version: v5
patch_series:
- version: v5
  msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
  date: 2026-11-08
  summary: 29 补丁：25 个 DL 带宽记账修复 + sched_debug + 3 自测
  review_outcome: Juri 对 26/29 Works for me；15/16/18 质疑由实测数据回应；v6 计划明确
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - v6（含 cpuset 拒绝补丁、rebuild 跳过优化、dl_departed_lock 等）待发布后评审
  next_action: 等待作者发布 v6 并继续评审
contribution_opportunities:
- kind: testing
  description: 在 Android 设备或 arm64 平台跑 patch 15 的 rebuild 遍历优化
- kind: review
  description: 核查 16/29 的 dl_departed_lock 是否覆盖全部 dl_bw_gen 竞态调用者
- kind: discussion
  description: 对 cpuset.cpus 拒绝语义提供 cgroup v1/v2 场景反馈（作者未测 v1）
generated_at: '2026-11-14T01:30:00'
source_email_count: 7
related_articles:
- sched-20261105-001
- sched-20261106-001
- sched-20261107-002
- sched-20261108-003
- sched-20261109-001
- sched-20261110-009
tags:
- deadline
- dl_server
- cgroup
title: 'sched/deadline: Move a task''s bandwidth only where room was made'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列（21 补丁）在 Juri Lelli 此前 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug，带自测与 sched_debug；Juri 已对多数给 Reviewed-by/Acked-by，Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261109-001</a>：v5 发出（29 补丁，25 修复 + sched_debug + 3 自测）。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-009-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261110-009</a>：Juri 评审 07/08/09，Mathieu 逐条回应并披露 v6 计划（新增 patch 28/29 修「0-lag 前带新参数返回」）。
- <a class="article-ref" href="/lkm/2026/11/13/sched-20261113-013-sched-deadline-move-a-task-s-bandwidth-only-where-room-was-m.html">sched-20261113-013</a>（今天）：**围绕 patch 15/16/18/26 收口**——Juri 对 26/29（sched_debug 展示每 rq deadline 带宽）表示「Works for me」；**Waiman Long 追问「cpuset 跨两个 root domain 是否可能」**，Mathieu 用 `isolcpus=domain` 的 5-CPU guest 实测说明该场景真实存在（并计划新增 cpuset 补丁拒绝这类迁移）；Mathieu 还披露 patch 15 的遍历成本实测（30000 线程单次 rebuild 2.3ms）与「无 deadline 任务时跳过遍历」的 v6 优化。

## 背景与问题
（承接 20261105-001 / 20261109-001 / 20261110-009）SCHED_DEADLINE 带宽记账（dl_bw / total_bw / this_bw / running_bw）存在多处边界缺陷，尤其与 cpuset 的 root domain 切换、isolcpus 交互时，任务带宽会被记到错误的 root domain 甚至「哪儿都没记」。v5 系列修复这些记账 bug。今日焦点是「任务带宽应归属哪个 root domain」这一记账前提，与 sched_debug 的暴露方式。

## 技术方案
今日围绕四个补丁：
- **18/29 `Move a task's bandwidth only where room was made`**：Waiman Long 质疑「cpuset 无法跨两个 root domain」；Mathieu 用 `isolcpus=domain,1,2` 的 5-CPU guest 实测说明：被隔离 CPU 仍在 top cpuset 的 effective CPUs 内、在 default root domain，其余 CPU 在另一 root domain——同一 cpuset 的两个 DL 任务（95 钉 0,3,4 要 10%、98 钉 1,2 要 20%）都被准入、带宽记到两个 root domain；把 95 迁到 CPU1 后其 10% 带宽「哪儿都不记」——正是该补丁修的 case。Mathieu 还计划新增 cpuset 补丁：cpuset.cpus 写操作若让 DL 任务在其计账 root domain 无 CPU 则拒绝（EBUSY），partition root 同理。
- **15/29 `Rebuild the root domains' accounting from the task list`**：Juri 指出无 deadline 任务时逐 task 遍历成本过高；Mathieu 实测（64-vCPU guest，无调试、无 deadline 任务）：30000 线程单次 rebuild 0.7-2.3ms，upstream 无 deadline 任务时早退故不随线程增长。v6 计划「系统无任务持 deadline 带宽时跳过遍历」，只维护一个全系统计数；优化后 rebuild 恒 0.03ms。并说明 Juri 提的「单一 accounted 列表」方案（0.03ms）因 rebuild 全程关中断、随 deadline 任务数增长而被放弃。
- **16/29 `Record the root domain holding a task's bandwidth`**：Juri 指出 `dl_bw_gen` 变化在 rebuild 时持 cpuset_mutex，而本补丁阶段其它调用者（`select_fallback_rq()`、关闭准入控制时的 `sched_setaffinity()`）不持锁，测试与 `__dl_sub()` 之间 `dl_bw_gen` 可能变；v6 计划用 `dl_departed_lock` 包住测试与记录更新。零带宽任务的特殊 case 保留现状（`move_zero_bw` 用例覆盖），拒绝「最小 1」以免改变准入（每任务一 CPU 的百万分之一）。
- **26/29 `sched/debug: Show the deadline bandwidth of each runqueue`**：Juri 表示「Works for me, thanks」；Mathieu 解释两行输出是为自测（`params_waking`/`random_mix` 读 running_bw/this_bw），selftest 不能依赖 drgn 与运行内核的调试信息，故保留该补丁、不加 `extra_bw`。

此外 Mathieu 回应 Andrea Parri：本系列 patch 18 与 Andrea 的 SCHED_DEADLINE 亲和性检查补丁重叠，属文本冲突、语义不矛盾，v6 会把 Andrea 的补丁原样放在 patch 18 之前携带。

## 版本演进与当前进展
v2（21 补丁）→ v3（24）→ v4（26）→ v5（29）→ 今日 patch 级评审收口，v6 计划明确（新增 cpuset 拒绝补丁、跳过无 deadline 任务的 rebuild 遍历、`dl_departed_lock` 包住 16/29 的更新、patch 28/29 修「0-lag 前带新参数返回」）。

## Maintainer 意见与讨论焦点
- **Juri Lelli（deadline 维护者）**：对 26/29 表示「Works for me」；对 15/16 的质疑已被 Mathieu 用实测数据回应。
- **Waiman Long**：对 18/29 的「cpuset 跨两个 root domain」前提提出质疑，Mathieu 给出 isolcpus=domain 复现实证。
- **Andrea Parri**：与 patch 18 的重叠已达成「下版携带」的协调。
- 无 NAK；pending 项为 v6 的一系列落地方案待发布后评审。

## 合入评估
维护者深度参与、分歧点逐一用数据收口，合入概率高；当前卡在 v6 发布与后续评审，无根本性 NAK。

## 效果评估
今日新增实测：patch 15 的 rebuild 遍历成本 0.04-2.3ms（0→30000 线程）、优化后恒 0.03ms；18/29 的 isolcpus=domain 复现（total_bw 从 fair server 的 157284/104856 增到 262141/314571，迁移后 10% 带宽「无处可记」）。均为作者实测。

## 我可以参与的点
- **testing**：在 Android 设备（作者明确点名欢迎）或其它 arm64 平台跑 patch 15 的 rebuild 遍历优化。
- **review**：核查 16/29 的 `dl_departed_lock` 是否覆盖全部 `dl_bw_gen` 竞态调用者。
- **discussion**：对「cpuset.cpus 写操作拒绝 DL 任务无计账 CPU」的语义提供 cgroup v1/v2 场景反馈（作者未测 cgroup v1）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261108185406.1549770-19-mathieu.desnoyers@efficios.com/
- 系列 cover（v5）: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
