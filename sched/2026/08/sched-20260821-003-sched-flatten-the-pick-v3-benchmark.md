---
id: sched-20260821-003
date: 2026-08-21
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: "<20260818091649.GC1247881@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/lkml/20260818091649.GC1247881@noisy.programming.kicks-ass.net/"
authors: ["Peter Zijlstra"]
maintainers_involved: ["Peter Zijlstra", "Srikar Dronamraju"]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20260818091649.GC1247881@noisy.programming.kicks-ass.net>"
    date: 2026-08-18
    summary: "v3 benchmark 验证，IBM 在 tip:sched/core 上重复测试"
    review_outcome: "IBM 提供 benchmark 结果，Xuewen Yan 提供测试脚本"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "需要更多硬件/负载场景的 benchmark 验证"
  next_action: "继续收集社区 benchmark 反馈"
contribution_opportunities:
  - kind: testing
    description: "在不同硬件上运行 sched messaging benchmark 并分享结果"
generated_at: "2026-08-21T10:00:00"
source_email_count: 1
related_articles: []
tags: ["sched/core", "cfs", "performance"]
---

## TL;DR

PeterZ 的"sched: Flatten the pick"系列 v3 讨论继续，IBM 工程师在 tip:sched/core 最新基线上重复了 benchmark，对比扁平 pick 层级与当前实现的性能差异。系列仍在 review 中。

## 背景与问题

这是 PeterZ 对调度器 pick 路径的重构系列，旨在扁平化 pick 层级结构，减少间接调用开销。该系列在前几天的邮件列表中首次出现（v1/v2），v3 带来了更多 benchmark 验证。

## 技术方案

将 `pick_next_task()` 的层级调用结构扁平化，直接在各调度类间选择，减少函数指针间接调用。这是对调度器核心路径的结构性优化。

## 版本演进与当前进展

- **v3** 讨论中：IBM 工程师（Srikar Dronamraju）在 `tip:sched/core` 最新基线（commit `85570f10a4c6` "sched/eevdf: Move to a single runqueue"）上 cherry-pick 了 flat hierarchy 修复（commit `68e3748781`），重复了 benchmark 测试。
- 基线对比：`4f166adb5cb0` (sched/fair: Fix flat hierarchy) vs 当前 tip

## Maintainer 意见与讨论焦点

讨论以 benchmark 验证为主，未出现明显分歧。IBM 团队积极参与测试验证。

## 合入评估

- **likelihood**: medium
- **blocking_issues**: 需要充分的 benchmark 验证覆盖各种负载场景
- **next_action**: 继续收集不同硬件/负载下的 benchmark 数据

## 效果评估

IBM 的 benchmark 使用 `coresched new -t pid -- perf bench sched messaging` 进行测试。具体数字未在邮件中完整披露，但测试框架脚本已分享。Xuewen Yan (ByteDance) 也提供了带宽测试脚本，使用 quota 设置触发问题场景。

## 我可以参与的点

- 在不同硬件配置（多 socket、NUMA、大小核）上运行 benchmark 并回帖分享结果
- 关注 pick 路径扁平化对延迟敏感型负载的影响

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260818091649.GC1247881@noisy.programming.kicks-ass.net/
- tip-bot commit: 未获取到
- stable backport: 未获取到
