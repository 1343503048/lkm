---
id: sched-20261112-009
date: '2026-11-12'
subject: 'sched/rt: Do not account migrate-disabled tasks as pushable'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <avXKCDm7NiVejDiF@techsingularity.net>
lore_url: https://lore.kernel.org/all/avXKCDm7NiVejDiF@techsingularity.net/
authors:
- Mel Gorman
- Yousaf Kaukab
maintainers_involved:
- Peter Zijlstra
- Steven Rostedt
current_version: v2
patch_series:
- version: v1
  msgid: <20261110232057.4144723-1-mgorman@techsingularity.net>
  date: '2026-11-10'
  summary: 三补丁：从 pushable 列表移除 migrate-disabled 任务、资格检查收拢、!RT_PUSH_IPI 保留
  review_outcome: Steven/Peter 建议折叠，作者采纳
- version: v2
  msgid: <avXKCDm7NiVejDiF@techsingularity.net>
  date: '2026-11-12'
  summary: 折叠为单补丁；Peter 追问 RT_PUSH_IPI 条件分支并请同步 DL
  review_outcome: Peter 细致评审中
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 质疑 RT_PUSH_IPI 条件分支是否应无条件化
  - DL 侧是否同步待论证
  next_action: 作者回应 Peter 的无条件化建议并论证/补齐 DL 侧一致性
contribution_opportunities:
- kind: review
  description: 核对无条件 is_migration_disabled 对 !RT_PUSH_IPI 架构的 pull 可达性影响
- kind: discussion
  description: 梳理 DL 侧 push 语义差异以判断 DL 是否应同步
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261111-002
tags:
- rt
- affinity
title: 'sched/rt: Do not account migrate-disabled tasks as pushable'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261111-002</a>：Mel Gorman 发三补丁修 RT 类 pushable 记账缺陷——migrate-disabled 任务仍被放进 pushable 列表并置起 `rq->rt.overloaded`，导致其它 CPU 的 pull IPI 反复命中「推不动」的任务、制造无效 IPI。刚发出时暂无回复。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-009-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261112-009</a>（今天）：**Steven Rostedt 建议把 patch 2/3 折叠进 patch 1**，Mel 同意折叠（「Yousaf 对折叠也无异议，我会把它们合成 1」）；**v2 发出并 Peter Zijlstra 评审**——问无条件保留 `is_migration_disabled()` 判断有何副作用，并请作者对 deadline 侧做同样处理（尽量保持 RT/DL 同步）。系列收敛为单补丁。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-002-sched-rt-do-not-account-migrate-disabled-tasks-as-pushable.html">sched-20261111-002</a>）`dae5c0292080` 修掉了 `pick_next_pushable_task()` 返回 migrate-disabled 任务的问题，但 `enqueue_task_rt()`/`put_prev_task_rt()` 仍把这些任务计为 pushable 并置起 `rq->rt.overloaded` 与 rto_mask，其它 CPU 每次 pull 触发的 IPI 可能只找到不可迁移的 migrate-disabled 任务。

## 技术方案

（承接 v1 三补丁）三补丁的拆分为「v1 作者保守起见」所致：patch 2 初衷是「降低未来只有 1 个调用点更新时产生 drift 的风险并顺带让 patch 3 略简单」、patch 3 是后补的「!RT_PUSH_IPI 场景保留原记账」。今日 Steven 与 Peter 都认为 2/3 复杂度不足以支撑单独成片，Mel 决定折叠成单补丁。v2 单补丁为：`enqueue_task_rt()`/`put_prev_task_rt()` 入列条件加 `&& !is_migration_disabled(p)`，并保留对 `!RT_PUSH_IPI` 配置的原记账语义。

## 版本演进与当前进展

*current_version: v2（2026-11-12，`<avXKCDm7NiVejDiF@techsingularity.net>`）*。v1（3 补丁）→v2（折叠为 1）：按 Steven Rostedt / Peter 的意见把「资格检查收拢」与「!RT_PUSH_IPI 保留」两片吸收进主补丁。触发场景仍是 RT 优先级、spinlock 密集的 `pgrep`。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：v2 评审——「无条件保留 `is_migration_disabled()` 判断有什么副作用吗？并请对 deadline 也做同样处理——我们尽量让 RT 与 DL 保持同步。」即 (a) 质疑 `!RT_PUSH_IPI` 的条件分支是否必要（倾向前一律不进列表）；(b) 要求 DL 侧同步（此前的 v1 刻意只改 RT）。
- **Steven Rostedt**：「看不出为何是 3 个补丁，patch 2/3 似乎可以折进 patch 1」。
- **Mel Gorman（作者）**：承认三补丁是 spi 保守拆分 + 后续检查副作用的产物，接受折叠；Yousaf Kaukab 对折叠无异议。
- 无 NAK。焦点转向「RT_PUSH_IPI 条件分支是否应无条件化」与「DL 侧是否同步」两个实质问题。

## 合入评估

*likelihood=high*。方向获 RT 维护者认可并已收敛为单补丁，Peter 在细致评审。*blocking_issues*：Peter 的「无条件化 + DL 同步」两点需作者回应（DL 侧此前有「push 是为顶走正运行任务、需单独论证」的既有理由）。*next_action*：作者回应 Peter 的 RT_PUSH_IPI 条件分支问题，并论证/补齐 DL 侧的一致性。

## 效果评估

作者未给量化数据；收益为消除「IPI 反复命中不可迁移任务」的无效开销，机制性正确性修复。

## 我可以参与的点

- **review**：核对「无条件 `!is_migration_disabled()`」对 `!RT_PUSH_IPI` 架构的影响——后者的 `pull_rt_task()` 没有 IPI、必须能找到 off-CPU migrate-disabled 任务的 rq，这是作者此前保留条件分支的理由，是否真有例外值得复核。
- **discussion**：梳理 DL 侧 push 与 RT 侧的语义差异（DL push 为顶走正运行任务、代价有界），帮助判断「DL 是否应同步」这一 Peter 的要求。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/avXKCDm7NiVejDiF@techsingularity.net/
- Peter 的评审: https://lore.kernel.org/all/20261112153120.GU1779021@noisy.programming.kicks-ass.net/
- Steven 的折叠建议: https://lore.kernel.org/all/20261112044642.0f28f038@fedora/
