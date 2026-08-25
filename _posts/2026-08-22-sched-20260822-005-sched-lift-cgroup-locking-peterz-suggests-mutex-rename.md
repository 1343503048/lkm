---
id: sched-20260822-005
date: 2026-08-22
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260821140818.1559100-1-michalblk@google.com>
lore_url: https://lore.kernel.org/lkml/20260821140818.1559100-1-michalblk@google.com/
authors:
- Michal Blaszczyk
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20260821140818.1559100-1-michalblk@google.com>
  date: 2026-08-21
  summary: v2 将 CFS 锁提升到 core 层
  review_outcome: PeterZ 建议锁重命名为 cpu_weight_mutex/cpu_max_mutex
upstream_commit: null
fixes_commit: '819513666966'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 作者出 v3 采用新命名
contribution_opportunities: []
generated_at: '2026-08-22T10:00:00'
source_email_count: 1
related_articles:
- sched-20260821-001
tags:
- sched/core
- sched_ext
- cgroup
title: 本文是 sched-20260821-001 的增量更新
layout: article
---

## TL;DR

本文是 sched-20260821-001 的增量更新。PeterZ 对 Michal Blaszczyk 的 v2 补丁提出命名建议：将锁重命名为 `cpu_weight_mutex` 和 `cpu_max_mutex`，使命名更精确反映锁保护的 cgroup 控制文件。

## 背景与问题

v2 补丁将 CFS 锁提升到 core 层，PeterZ 认可方向但建议改进锁的命名。

## 技术方案

将通用的 "cgroup lock" 命名改为更精确的 `cpu_weight_mutex`（保护 cpu.weight/cpu.shares 写入）和 `cpu_max_mutex`（保护 cpu.max 写入）。

## 版本演进与当前进展

PeterZ 的命名建议刚发出，等待作者 v3 响应。

## Maintainer 意见与讨论焦点

PeterZ: "Maybe cpu_weight_mutex? and cpu_max_mutex?"

方向认可，仅命名改进。

## 合入评估

- **likelihood**: high（与 sched-20260821-001 一致）
- **blocking_issues**: 无
- **next_action**: 作者出 v3 采用新命名

## 效果评估

无变化。

## 我可以参与的点

同 sched-20260821-001。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821140818.1559100-1-michalblk@google.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
