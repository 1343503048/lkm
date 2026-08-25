---
id: sched-20260818-003
subject: '[GIT PULL] sched_ext: Changes for v7.3'
date: 2026-08-18
subsystem: sched
type: feature
status: merged_tip
severity: high
thread_root_msgid: <29c6986172b4eb9ba292643ab4ad9583@kernel.org>
lore_url: https://lore.kernel.org/r/29c6986172b4eb9ba292643ab4ad9583@kernel.org
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <29c6986172b4eb9ba292643ab4ad9583@kernel.org>
  date: 2026-08-18
  summary: sched_ext for v7.3 GIT PULL：完成层级子调度的 CPU 委派、rescue execution、core scheduling
    修复。
  review_outcome: GIT PULL 已发出，等待 Linus 收下。
upstream_commit: fab183d632628381b466a41479489541ac0e29a0
fixes_commit: null
merged_branch: sched_ext/for-7.3
merge_assessment:
  likelihood: high
  blocking_issues:
  - 依赖 BPF pull 和 scheduler core pull 先合入
  next_action: 等待 Linus 在 v7.3 merge window 收下。
contribution_opportunities: []
generated_at: '2026-08-19T00:10:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- sched/core
title: 'sched_ext: Changes for v7.3'
layout: article
---

## TL;DR
Tejun Heo 发出 sched_ext for v7.3 的 GIT PULL 请求。本轮主要完成层级子调度（hierarchical sub-scheduling）的 CPU 委派功能，使 sub-scheduler 功能完整：root BPF 调度器可将 cgroup 子树连同可撤销 CPU 授予交给嵌套子调度器。依赖 BPF 树的 arena argument 支持，需在 scheduler core 和 BPF pull 之后合入。

## 背景与问题
sched_ext v7.2 已合入层级子调度的基础框架，但 CPU 委派仅限于 dispatch 层面。v7.3 周期将委派扩展到完整 CPU 能力（enqueue、preemption、CPU frequency control），使子调度器能完全控制其 CPU。此外还引入了 rescue execution（任务在调度器无法访问的 CPU 上饿死时由内核直接运行）和 core scheduling 修复。

## 技术方案
- **Sub-scheduler CPU delegation**：父调度器向子调度器授予/撤销 per-CPU 能力（enqueue、preemption、CPU frequency control），在每条调度器可达 CPU 的路径上强制执行。此前仅 dispatch 可委派。
- **Rescue execution**：任务的调度器无法访问其所需 CPU 时，内核直接在小带宽窗口运行该任务，避免 watchdog 踢出整个调度器。
- **Core scheduling fixes**：v7.2 发布前未完成的核心调度修复，经此 pull request 路由。
- 依赖 BPF 树的 arena argument 支持，需先合入 scheduler core 和 BPF pull。

## 版本演进与当前进展
- GIT PULL 已发出（2026-08-18），tag `sched_ext-for-7.3`。
- 基于 bpf-next 的 patch 此前保持在独立分支，现已合并入 for-7.3。
- 同一合并结果已在 linux-next 测试数天。

## Maintainer 意见与讨论焦点
- Tejun Heo 作为 sched_ext maintainer 发出 pull request。
- 依赖 BPF 树的 arena argument 支持，需 Linus 在合并 scheduler core 和 BPF 后收下。

## 合入评估
GIT PULL 已发出，等待 Linus 收下。依赖链：BPF pull → scheduler core pull → sched_ext pull。预计 v7.3 merge window 期间合入。

## 效果评估
暂无独立 benchmark。Pull request 描述"development volume was high and a number of changes plugging holes in the new support landed late in the cycle"。

## 我可以参与的点
- 当前阶段为 pull request 等待合入，暂无明显参与空间。可持续关注 v7.3-rc1 合并后的测试结果。

## 参考链接
- lore thread: https://lore.kernel.org/r/29c6986172b4eb9ba292643ab4ad9583@kernel.org
- git tree: https://git.kernel.org/pub/scm/linux/kernel/git/tj/sched_ext.git tags/sched_ext-for-7.3
- tip-bot commit: 未获取到
- stable backport: 未获取到
