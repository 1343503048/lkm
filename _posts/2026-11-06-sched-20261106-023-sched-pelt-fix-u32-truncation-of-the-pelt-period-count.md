---
id: sched-20261106-023
date: 2026-11-06
subject: 'sched/pelt: Fix u32 truncation of the PELT period count'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <179395863661.1009794.3409769608044766882.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179395863661.1009794.3409769608044766882.tip-bot2@tip-bot2/
authors:
- Hui Su
maintainers_involved:
- Ingo Molnar
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261023025207.2967903-1-sh_def@163.com>
  date: 2026-10-23
  summary: accumulate_sum 返回类型 u32 改 u64，避免周期数截断。
  review_outcome: Vincent/Kayra 双 Reviewed-by；11-06 合入 tip/sched/urgent。
upstream_commit: a0c755e574e37fddb59edf175f27dc3877e7fe23
fixes_commit: a481db34b9be
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 进入主线
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261023-006
tags:
- cfs
- perf
title: 'sched/pelt: Fix u32 truncation of the PELT period count'
layout: article
---

## TL;DR

Hui Su 的修复今日合入 tip/sched/urgent（commit `a0c755e574e37fddb59edf175f27dc3877e7fe23`）：`accumulate_sum()` 用 u64 计算已流逝的 PELT 周期数、却以 u32 返回，当周期数是 2^32 的整数倍（约 50 天不更新）时被截断为 0，调用方误判「无周期边界」跳过平均值重算，`*_avg` 相对 `*_sum` 陈旧。修复把返回类型改为 u64。此前已获 Vincent Guittot 与 Kayra Cizmeci 双 Reviewed-by。

## 背景与问题

`accumulate_sum()` 内部用 u64 计算 `delta` 对应的 PELT 周期数，但函数签名返回 u32。当周期数恰为 2^32 的倍数时截断成 0，调用方 `___update_sched_avg()` 据此认为没有跨周期边界、跳过 `*_avg` 重算——尽管 `*_sum` 已更新，二者从此失配。

## 技术方案

把 `accumulate_sum()` 的返回类型从 `static __always_inline u32` 改为 `static __always_inline u64`，调用方可无损地测试周期数是否非零。改动 `kernel/sched/pelt.c` 仅 1 行。

## 版本演进与当前进展

*current_version: v2（2026-10-23 发出）*。v1 返回 `!!periods`；v2 按 K Prateek Nayak 建议改返回 u64 并补 `Fixes`、带 Kayra 的 Reviewed-by。今日合入 tip/sched/urgent。

## Maintainer 意见与讨论焦点

Vincent Guittot（sched/fair 维护者）与 K Prateek Nayak、Kayra Cizmeci 均 review，双 Reviewed-by 背书，无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，commit `a0c755e574e37fddb59edf175f27dc3877e7fe23`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线。

## 效果评估

无量化数据（正确性修复：周期数不再被 u32 截断，避免约 50 天不更新场景下的 `*_avg` 陈旧）。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/a0c755e574e37fddb59edf175f27dc3877e7fe23
- 原补丁 lore: https://patch.msgid.link/20261023025207.2967903-1-sh_def@163.com
