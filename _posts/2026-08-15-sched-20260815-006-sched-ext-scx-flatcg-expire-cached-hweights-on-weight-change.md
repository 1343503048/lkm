---
id: sched-20260815-006
date: 2026-08-15
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <uid-41267@qq-imap>
lore_url: 未获取到
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <uid-41267@qq-imap>
  date: 2026-08-15
  summary: 修复 scx_pair / scx_flatcg 中 cvtime 钳制与 hweight 一致性的 'true-up'：consume 时给
    cvtime 增加下限钳制。
  review_outcome: Tejun 已 apply（'Applied to sched_ext'），并反馈后续会做更大重构。
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入；等待 Tejun 的层级权重重构落地。
contribution_opportunities:
- kind: discussion
  description: 可关注 Tejun 提到的后续 '层级权重' 重构方向，提前理解 scx_flatcg 演进。
generated_at: '2026-08-16T00:10:00'
source_email_count: 2
related_articles:
- sched-20260815-007
tags:
- sched_ext
- sched/cache
title: 'sched_ext/scx_flatcg: expire cached hweights on weight changes'
layout: article
---

## TL;DR
Tao Cui 的 `cvtime` true-up 补丁：修复 `scx_pair`/`scx_flatcg` 中 cvtime（消费虚拟时间）钳制与 hweight（层级权重）不一致的问题——consume 时给 cvtime 增加下限钳制。已 apply 到 sched_ext（Tejun 称后续会做更大重构）。

## 背景与问题
`scx_flatcg`/`scx_pair` 用 cvtime 跟踪 cgroup 层级的消费进度，并用 hweight 表达层级权重。若 cvtime 在 consume 时未被恰当钳制，会与当前 hweight 配置不一致，导致层级公平调度出现偏差（如权重分配失真）。

## 技术方案
- 在 consume 路径为 cvtime 增加下限钳制，使其与 hweight 配置保持 true-up（一致）。
- 注释同步说明 cvtime 与 hweight 的关系。
- 改动集中在 `scx_flatcg`/`scx_pair` 用户态 BPF 调度器代码。

## 版本演进与当前进展
v1（41267）于 2026-08-15 发出，作为对 41396（之前 flatcg 重构）的 follow-up。Tejun 回复 "Applied to sched_ext"，并说明后续会有涉及层级权重的"更大重构"，本 true-up 作为临时正确化先合入。

## Maintainer 意见与讨论焦点
- Tejun Heo：apply 到 sched_ext，并提示 006 只是临时 true-up；真正的修复是后续对层级权重计算的重构（与 007 系列的"expire cached hweights"讨论相关）。

## 合入评估
已合入 sched_ext。无悬空问题。后续被更大重构取代属计划内。

## 效果评估
修正层级公平调度中 cvtime 与 hweight 不一致导致的偏差；无性能数据，纯正确性修复。

## 我可以参与的点
- 关注 Tejun 计划的"层级权重重构"，理解 scx_flatcg 未来走向。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
