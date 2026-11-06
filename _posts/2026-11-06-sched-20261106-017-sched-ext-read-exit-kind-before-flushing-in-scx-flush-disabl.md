---
id: sched-20261106-017
date: 2026-11-06
subject: 'sched_ext: Read exit_kind before flushing in scx_flush_disable_work()'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261104111449.3984318-1-jpiecuch@google.com>
lore_url: https://lore.kernel.org/all/20261104111449.3984318-1-jpiecuch@google.com/
authors:
- jpiecuch@google.com
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261104111449.3984318-1-jpiecuch@google.com>
  date: 2026-11-04
  summary: scx_flush_disable_work 中先读 exit_kind 再 flush。
  review_outcome: Tejun 应用至 sched_ext/for-7.4-fixes，补 Andrea Righi Reviewed-by。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 sched_ext 修复 pull request 到主线
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Read exit_kind before flushing in scx_flush_disable_work()'
layout: article
---

## TL;DR

jpiecuch@google.com 的 sched_ext for-7.4-fixes 修复（补丁本体系 11-04 发出、未在本日缓存内）：`scx_flush_disable_work()` 里应在 flush 之前读取任务的 exit_kind，避免禁用流程中读到已变化的状态。今日 Tejun Heo 回复「Applied to sched_ext/for-7.4-fixes」，并补上 Andrea Righi 的 Reviewed-by——该修复已进 sched_ext 修复分支。

## 背景与问题

补丁正文未在本日邮件缓存中（本缓存仅含 Tejun 的「Applied」回复），具体触发条件与症状未获取到。从标题与 for-7.4-fixes 归属可判断：这是 `scx_flush_disable_work()` 在 flush 前后对 `exit_kind` 的读取顺序问题——任务退出期间其 exit_kind 可能被改写，若在 flush 之后才读，会用到过期值。

## 技术方案

在 `scx_flush_disable_work()` 中先读取任务的 exit_kind、再做 flush（具体 diff 未获取到，见参考链接）。

## 版本演进与当前进展

*current_version: v1（2026-11-04 发出）*。今日（11-06）Tejun Heo 应用该补丁到 sched_ext/for-7.4-fixes，并补 Andrea Righi 的 Reviewed-by。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）已应用（Applied），Andrea Righi 已给 Reviewed-by。无异议。

## 合入评估

*likelihood=high*。已应用进 sched_ext/for-7.4-fixes 分支（`merged_branch=sched_ext/for-7.4-fixes`），随 Tejun 的 sched_ext 修复 pull 进入主线。*blocking_issues*：无。*next_action*：等待 sched_ext 修复 pull request 到主线。

## 效果评估

暂无效果数据（补丁正文未获取到）。

## 我可以参与的点

当前阶段暂无明显参与空间：修复已进 sched_ext 修复分支，等待 pull。

## 参考链接

- lore thread（原补丁）: https://lore.kernel.org/all/20261104111449.3984318-1-jpiecuch@google.com/
- Tejun 的 Applied 回帖: https://lore.kernel.org/all/4f5f54504fb1221d07ffb6d66b9f449d@kernel.org/
