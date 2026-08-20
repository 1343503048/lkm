---
id: sched-20260804-014
date: 2026-08-04
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Hongling Zeng
maintainers_involved:
- Peter Zijlstra
- Mel Gorman
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-04
  summary: 'update_task_scan_period() 在迁移失败（slow-scan 路径）early return 前未清零 locality
    统计，导致同一迁移失败反复选 slow-scan 直到最大扫描周期。补上 memset 清零，与正常路径一致。Fixes: f307cd1a32fa，Cc:
    stable。'
  review_outcome: v1 刚发，有 Fixes + stable Cc，尚未见 maintainer 回复。
upstream_commit: null
fixes_commit: f307cd1a32fa
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 PeterZ/Mel 接收；有 Fixes + stable，阻力小。
contribution_opportunities:
- kind: testing
  description: 可在 NUMA 迁移失败频发的负载下验证 early-return 后扫描周期不再被拖到最大值，回帖验证数据。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles: []
tags:
- numa
- scan_period
- sched_debug
title: 'sched/numa: Fix scan period for remote private faults'
layout: article
---

# sched/numa: early return 时清零 locality 统计

## TL;DR
`update_task_scan_period()` 在迁移失败（slow-scan 路径）early return 前未清零 locality 统计，导致同一迁移失败反复选 slow-scan、把扫描周期拖到最大。Hongling Zeng 补上清零，与正常路径一致。Fixes + stable，合入可能性 high。

## 背景与问题
`update_task_scan_period()` 在「无 NUMA hinting fault 记录」时走 slow-scan 路径并 early return。但 early return 前没有像正常路径那样清零 `numa_faults_locality`，导致**非空的 locality 统计**使后续扫描周期更新持续走 slow-scan 分支，直到达到最大扫描周期——即一次迁移失败的影响被错误放大、长期拖慢该任务的 NUMA 扫描。

## 技术方案
在 slow-scan 路径 early return 前 `memset(p->numa_faults_locality, 0, ...)`，与正常路径的清理一致，使后续扫描周期更新能用上干净的 locality/migration 统计。标注 `Fixes: f307cd1a32fa` 与 `Cc: stable`。

## 版本演进与当前进展
v1（2026-08-04），作者 Hongling Zeng（同 08-04-013 同作者，均为 numa 扫描修正）。

## Maintainer 意见与讨论焦点
尚未见 maintainer 回复。有 Fixes + stable Cc，属典型应快速接收的小修正。

## 合入评估
合入可能性 high。有 Fixes + stable，无功能风险。

## 效果评估
邮件未附 benchmark，是正确性修复（消除 slow-scan 被错误长期拖慢）。可用 NUMA 迁移失败负载验证，作者未附 runs。

## 我可以参与的点
- 在 NUMA 迁移失败频发负载下验证 early-return 后扫描周期不再被拖到最大值，回帖验证数据。

## 参考链接
- lore thread: 未获取到
