---
subject: '[PATCH v10 00/12] sched, steal_governor: Introduce preferred CPUs and steal-driven
  vCPU backoff'
id: sched-20260814-004
date: 2026-08-14
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260814190858.steal_gov@shrikanth>
lore_url: 未获取到
authors:
- Shrikanth Hegde
- Mete Durlu
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Ionut Neagu
- Yury Norov
- Mete Durlu
current_version: v10
patch_series:
- version: v10
  msgid: <20260814190858.steal_gov@shrikanth>
  date: 2026-08-14
  summary: v10（12 patches）steal_governor：引入 preferred CPUs 与 steal-driven vCPU backoff。8/14
    讨论聚焦是否应为 s390 等架构抽象出 cpuidle 式框架（init/exit/ops），Mete 表示 s390 计划采用 preferred CPU
    方案并可能自带 governor 模块；最终决定先简单合入、post-merge 再拆分框架。
  review_outcome: Shrikanth 与 Mete 就架构特定钩子（s390）达成先简单合入、后续拆分框架的一致；Shrikanth 表示若 Ionut/Yury
    不回将下周发 v11。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 等待 Ionut/Yury 对全部评论的回应；架构特定框架 post-merge 拆分
  next_action: 若无回应，Shrikanth 下周发 v11；届时再推进合入。
contribution_opportunities:
- kind: review
  description: 评审 steal_governor 默认实现与未来架构特定模块（s390）的拆分方案。
- kind: discussion
  description: 参与 cpuidle 式框架 vs __weak vs 多模块 三种拆分方式的取舍讨论。
generated_at: '2026-08-15T00:15:00'
source_email_count: 4
related_articles:
- sched-20260810-008
tags:
- sched/core
- affinity
title: 'Re: [PATCH v10 00/12] sched, steal_governor: Introduce preferred CPUs and
  steal-driven vCPU backoff'
layout: article
---

## TL;DR
Shrikanth Hegde 的 steal_governor v10（12 patches，preferred CPUs + steal-driven vCPU backoff）在 8/14 与 Mete 讨论架构特定抽象（s390 计划采用并可能自带 governor 模块）。决定先简单合入、post-merge 再拆框架。under_review。

## 背景与问题
steal_governor 是一个调度子系统，用于「窃取」空闲 CPU 周期（面向虚拟化 vCPU 回退场景），并引入 preferred CPUs 管理。当前实现为单一内建 governor，但 s390 等架构计划采用 preferred CPU 方案并可能自带 governor 模块，需要更清晰的架构/平台特定抽象。

## 技术方案
v10 主线：preferred CPUs 管理 + steal-driven vCPU backoff。讨论中的未来框架（post-merge）三选一：① ifdefs + ops 函数指针；② __weak 函数（最小样板，但非首选）；③ 多模块（steal_governor_core.ko + steal_governor_s390.ko，core 导出 register_driver 符号）。当前决定：先保留简单单文件实现合入，待采纳后再拆。

## 版本演进与当前进展
当前 v10（12 patches）。8/14 讨论确认先简单合入；Shrikanth 表示若 Ionut/Yury 几天内不回应将发 v11。

## Maintainer 意见与讨论焦点
Mete（s390）希望有类似 cpuidle 的公共基础设施（init/exit/方法）只把决策留给架构；Shrikanth 同意但主张 post-merge 拆分。核心分歧已收敛为「先合入后拆分」。

## 合入评估
合入可能性 medium。方向被接受，待所有评论回应与可能的 v11。

## 效果评估
无 benchmark；目标为虚拟化场景更优的 vCPU 回退/窃取策略。

## 我可以参与的点
- 评审架构特定框架三种方案；
- 跟踪 v11 与 s390 模块计划。

## 参考链接
- lore: 未获取到
- 关联: preferred CPU（见 sched-20260810-008）
