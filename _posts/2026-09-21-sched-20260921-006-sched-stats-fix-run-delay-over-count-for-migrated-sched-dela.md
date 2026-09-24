---
id: sched-20260921-006
date: '2026-09-21'
subject: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260920043116.1298017-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20260920043116.1298017-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20260920043116.1298017-1-albin_yang@163.com>
  date: '2026-09-20'
  summary: 正确结算迁移后 sched_delayed 任务的 run_delay，消除跨 CPU 多计数
  review_outcome: K Prateek Nayak Reviewed-by + Tested-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 sched 维护者 pickup 合入 tip/sched/core
contribution_opportunities: []
generated_at: '2026-09-22T01:10:00'
source_email_count: 1
related_articles:
- sched-20260920-001
tags:
- cfs
title: 'sched/stats: Fix run_delay over-count for migrated sched_delayed tasks'
layout: article
---

## TL;DR
增量更新：Wei Yang 的 `sched/stats` run_delay 多计数修复（v2）昨日又获 K Prateek Nayak 的 Reviewed-by + Tested-by，评审背书进一步加强，合入概率高。

## 背景与问题
背景见 sched-20260919-004 / sched-20260920-001：任务在被迁移且处于 `sched_delayed`（延迟出队）状态时，`run_delay` 统计会被重复累计，导致 `/proc/<pid>/sched` 等接口里 run_delay 数据偏大失真。

## 技术方案
本日无新代码，是 v2 的评审推进。修复思路仍为对迁移到别的 CPU 的 sched_delayed 任务正确结算 run_delay 增量，避免跨 CPU 迁移路径上的重复计数。

## 版本演进与当前进展
- v1 → v2（09-20，thread root `<20260920043116.1298017-1-albin_yang@163.com>`）。
- 09-21：K Prateek Nayak 明确给出 `Reviewed-by` 与 `Tested-by`（"Feel free to include"）。

## Maintainer 意见与讨论焦点
- **K Prateek Nayak（AMD 调度资深开发者）**：给出 Reviewed-by + Tested-by，表明代码审阅通过且已实测验证，无异议。

## 合入评估
*likelihood=high*。统计类缺陷修复、影响面清晰、已有资深开发者审阅并实测背书，v2 无争议。*next_action*：等待 sched/stats 维护者（或 tip 树的 sched/core 维护者）pickup 合入。

## 效果评估
无具体数字；修复定性为消除 `run_delay` 的多计数，使统计回归真实（K Prateek 已实测验证）。

## 我可以参与的点
当前阶段暂无明显参与空间（已有 Rb/Tb 背书，只差维护者 pickup），可持续观察是否进入 tip/sched/core。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260920043116.1298017-1-albin_yang@163.com/
