---
id: sched-20261112-012
date: '2026-11-12'
subject: 'sched/deadline: Keep departing bandwidth across a root domain rebuild'
subsystem: sched
type: fix
status: under_review
severity: critical
thread_root_msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved:
- Juri Lelli
- Peter Zijlstra
current_version: v5
patch_series:
- version: v5
  msgid: <20261108185406.1549770-1-mathieu.desnoyers@efficios.com>
  date: '2026-11-08'
  summary: 29 补丁：25 个 DL 带宽记账修复 + sched_debug + 3 自测
  review_outcome: Juri 再给 17/19/24/25 Reviewed-by；13/29 irqoff 之争延续；v6 待发
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 15/29 需 Android 侧确认
  - 17/29 的 Fixes 标签待修正
  - 13/29 关中断权衡待定
  next_action: 发 v6 并等 Android 侧对 15/29 的表态、ping Tejun/Waiman 评审 cpuset 部分
contribution_opportunities:
- kind: testing
  description: 在 Android/等效环境复测 15/29 suspend/resume 无回归
- kind: review
  description: 复核 17/29 Fixes 修正与 18/29 flag 值 0x10 语义
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 8
related_articles:
- sched-20261105-001
- sched-20261106-001
- sched-20261107-002
- sched-20261108-003
- sched-20261109-001
- sched-20261110-009
- sched-20261111-006
tags:
- deadline
- cgroup
title: 'sched/deadline: Keep departing bandwidth across a root domain rebuild'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261105-001</a>：Mathieu Desnoyers 的 v2 系列在 Juri Lelli 的 4 个 sched/urgent 修复之上再修 17 个 SCHED_DEADLINE 带宽记账 bug（3 个可直接打死内核）。Ingo 要求「严格只含 -stable 可回退修复的子集」。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.html">sched-20261106-001</a> / 20261107-002 / 20261108-003 / 20261109-001 / 20261110-009：v3→v5 演进到 29 补丁，Juri 逐 patch 评审 03-09。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-006-sched-deadline-keep-departing-bandwidth-across-a-root-domain.html">sched-20261111-006</a>：Juri 评审 patch 11-16，13/29 提出单链表替代方案（Mathieu 实做后否决，rebuild 快 8 倍但关中断随任务数增长）。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-012-sched-deadline-keep-departing-bandwidth-across-a-root-domain.html">sched-20261112-012</a>（今天）：**Juri 评审 patch 17-19、24-26——17/19/24/25 给 Reviewed-by**（17 附「Fixes 标签需前置补丁才能成立」的修正、19 提醒需 ping Tejun/Waiman）；18/26 各一处 nit（flag 值 `0x10` 与 `dl_bw_dump.py` 提示）。**13/29 的关中断延迟之争延续**：Mathieu 追问 10k 任务、1.2ms vs 0.3ms 的 irqoff 是否对 PREEMPT_RT 有意义，Peter 回「这是 domain rebuild，谁在乎性能」。

## 背景与问题

（承接 20261105-001 … 20261111-006）Mathieu 系统梳理 dl_bw/total_bw/this_bw 记账边界缺陷的 v5（29 补丁）。今日评审进入收尾：17-26 号补丁多是收口性修复（dying task、带宽迁移、replenishment timer、boost 带宽计数、debug 展示），同时 13/29 的「root domain rebuild 是否该在关中断里遍历所有任务」的架构分歧仍在。

## 技术方案

今日无新代码，为逐 patch 评审：

- **17/29 `Leave a dying task out of a rebuild of the accounting`**：Juri 指出其 `Fixes` 标签不能单独应用（需前面至少 2 个补丁），除此之外给 Reviewed-by。
- **18/29 `Move a task's bandwidth only where room was made`**：Juri 问 flag 值为何不用 `0x10`，并指出注释与其它无注释 flag 不一致（`SCA` 含义记不清）。
- **19/29 `cgroup/cpuset: Wait for an attach before rebuilding the sched domains`**：Juri Reviewed-by，并提醒这是 cgroup/cpuset 域，需 ping Tejun/Waiman。
- **24/29 `Cancel the replenishment timer with the parameters`**：Reviewed-by。
- **25/29 `Count the bandwidth a boosted task is given`**：Reviewed-by，附「sugov 整个机制仍是 hack，但至少这次更不容易破坏准入控制」。
- **26/29 `Show the deadline bandwidth of each runqueue`**：Juri 认可但指出仍未打印 `extra_bw` 等，提示有 `tools/sched/dl_bw_dump.py` drgn 脚本可参考。

## 版本演进与当前进展

*current_version: v5（2026-11-08，`<20261108185406.1549770-1-mathieu.desnoyers@efficios.com>`）*。无新版本；今日又 5 个补丁获 Reviewed-by（17/19/24/25 加 17 修正），系列评审接近完成。13/29 的关中断争议仍在，v6 计划此前已明确。

## Maintainer 意见与讨论焦点

- **Juri Lelli（deadline 维护者）**：密集收口评审——17/19/24/25 给 Reviewed-by，17 的 Fixes 标签需改（不能单独应用）、18 的 flag 值 `0x10` 与注释待澄清、19 需 ping cpuset 维护者、26 建议参考 `dl_bw_dump.py`。
- **Mathieu Desnoyers（作者）**：对 13/29 追问 irqoff 延迟的三个问题（10k deadline 任务是否现实、1.2ms vs 0.3ms 关中断在 PREEMPT_RT 上是否相关、domain rebuild 是否会发生在有实时约束的系统上）。
- **Peter Zijlstra**：对 13/29 的 irqoff 顾虑不以为然——「这是 domain rebuild？我们真的在乎那里的性能吗？」。
- 无 NAK。分歧集中在 13/29「是否值得为消除 per-task 记账复杂度而接受 rebuild 期间的关中断延迟」这一架构权衡。

## 合入评估

*likelihood=high*。系列多数补丁已获 Juri Reviewed-by/Acked-by，今日又收口 5 个，v6 计划明确；13/29 的 irqoff 之争是架构偏好而非正确性阻塞，15/29 的 Android 确认仍待落实。*blocking_issues*：15/29 需 Android 侧确认；17/29 的 Fixes 标签待修正；13/29 的关中断权衡待定（Peter 倾向可接受）。*next_action*：作者发 v6（修 17 的 Fixes、采纳 18 的 flag 注释），等 Android 侧对 15/29 的表态，并 ping Tejun/Waiman 评审 19/29 的 cpuset 部分。

## 效果评估

无当日新增 benchmark。13/29 的关中断数据此前已给出（64-vCPU guest：1000 任务 0.75ms、10000 任务 7.4ms）。系列整体为正确性修复（部分可致内核 panic），无性能收益诉求。

## 我可以参与的点

- **testing**：在 Android 或等效「suspend/resume + SCHED_DEADLINE」环境复测 15/29，确认无 10-20ms 回归（Juri 点名要的确认）。
- **review**：复核 17/29 的 Fixes 标签修正（确认它依赖的前置补丁清单），以及 18/29 flag 值 `0x10` 的语义是否与既有 flag 编码一致。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261108185406.1549770-1-mathieu.desnoyers@efficios.com/
- Mathieu 对 13/29 的 irqoff 追问: https://lore.kernel.org/all/83b2244c-f68a-4af3-9c8f-0fabb4eacbb4@efficios.com/
- Juri 对 19/29 的 Reviewed-by: https://lore.kernel.org/all/avVvt8wlKqW4LqTa@jlelli-thinkpadt14gen4.remote.csb/
