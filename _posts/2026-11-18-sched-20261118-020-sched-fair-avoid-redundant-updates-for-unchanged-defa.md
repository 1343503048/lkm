---
id: sched-20261118-020
date: '2026-11-18'
subject: 'sched/fair: Avoid redundant updates for unchanged default slices'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: null
lore_url: null
authors:
- Chengfeng Lin
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series: []
upstream_commit: 9dc6cae4904ff34025704041d07c731937db10dc
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 观察随 sched/core 进入下一 mainline 合入窗口
contribution_opportunities: []
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- perf
title: 'sched/fair: Avoid redundant updates for unchanged default slices'
layout: article
---

## TL;DR

Chengfeng Lin 的性能优化**今日合入 tip/sched/core**（commit `9dc6cae4904f`，Committer Peter Zijlstra）：`_sched_setscheduler()` 对使用默认 slice 的 fair 任务，此前 `attr.sched_runtime=0` 与 `se.slice` 直接比较恒不相等，导致一个「参数未变的 `sched_setparam()`」也走完整参数更新路径。补丁先比较 default/custom 模式、再比较时长，并覆盖「custom slice 恰等于默认」「遗留请求需重置隐式 uclamp」两个边界。i7-12700KF 上每次 `sched_setparam` 从 616.51ns 降到 162.39ns。

## 背景与问题

对使用默认 slice 的 fair 任务，`_sched_setscheduler()` 把 `attr.sched_runtime` 保持为 0，而 `se.slice` 存的是实际时长——直接比较两者，会让一个「未变的 `sched_setparam()`」请求错误地进入参数更新路径（多余工作）。此外仅比较 runtime 相等还漏两个 case：custom slice 恰等于默认时需切换到 custom 模式、未变的遗留请求在 RT-PI boost 结束后可能仍需重置隐式 uclamp。

## 技术方案

按 Peter 建议：先比较 default/custom 模式，再比较请求时长；default 模式请求还检查任务 slice 是否仍匹配当前默认。更新路径保持在 fair 类之外、以及「隐式 uclamp 需重置」的情形；显式 uclamp 请求继续走既有路径。

## 版本演进与当前进展

已合入 tip/sched/core（`9dc6cae4904f`，AuthorDate 2026-10-19，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：作为 Committer 合入（正文引用其「先比较 default/custom 模式」的建议）。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/core（`9dc6cae4904f`）。*blocking_issues*：无。*next_action*：观察随 sched/core 进入下一 mainline 合入窗口。

## 效果评估

i7-12700KF（v7.2）上重复 `sched_setparam(0, priority=0)`（SCHED_OTHER nice-0）：每次调用 616.51ns → 162.39ns。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/9dc6cae4904ff34025704041d07c731937db10dc
- patch Link: https://lkml.iu.edu/2610.1/11150.html
