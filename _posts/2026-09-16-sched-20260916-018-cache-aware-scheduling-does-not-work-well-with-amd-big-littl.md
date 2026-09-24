---
id: sched-20260916-018
date: '2026-09-16'
subject: Cache-aware scheduling does not work well with amd big/little cores
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info>
lore_url: https://lore.kernel.org/all/2180ea5a-eb28-4152-8d4d-cd00b0c24b2e@computerix.info/
authors:
- Klaus Kusche
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: Intel 侧确认机制并把改动收敛进 cache-aware 系列
contribution_opportunities:
- kind: testing
  description: 在同类 AMD big/little 平台复测构建负载确认差距闭合
- kind: discussion
  description: 评估动态禁用 vs 修复选核逻辑两条路线的取舍
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles:
- sched-20260914-001
tags:
- load_balance
title: Cache-aware scheduling does not work well with amd big/little cores
layout: article
---

## TL;DR
本日为增量更新：报告者 Klaus Kusche 反馈 Intel 侧（Chen Yu）最新一版补丁后，其 AMD big/little（大小核混合）平台上 cache-aware 调度的性能已基本追平无 cache-aware 的内核，比早期 cache-aware 内核快约 2%，核心柱状图上也未见明显错放进程。这是一个偏正面的修复确认，完整背景见 related_articles。

## 背景与问题
原始问题是：cache-aware 调度在 AMD big/little（Zen4/Zen4c 混合架构，如 1CCX 大小核混排）平台上表现不佳——进程被错放到不适合的核心上，导致构建类负载变慢。线程的完整技术背景见 sched-20260914-001。

## 技术方案
Intel 侧（Chen Yu 等）针对该问题的补丁迭代（本日未在邮件正文给出具体 patch，Klaus 只引用了「你的上一个补丁」）。Klaus 不确定该补丁是否通过动态禁用大小核平台上的 cache-aware 调度来生效。

## 版本演进与当前进展
- 本日（107581）Klaus 回复 Chen Yu：两个构建测试在带 cache-aware 调度的内核上与无 cache-aware 内核几乎同速，比早期 cache-aware 内核约快 2%；核心柱状图未见明显错放进程。

## Maintainer 意见与讨论焦点
- **Klaus Kusche（报告者）**：确认最新补丁效果良好（约 +2% 于早期 cache-aware 内核），但不确定补丁的具体作用机制（是否动态禁用大小核上的 cache-aware）。
- 无新分歧；这是修复方向的正面数据。

## 合入评估
*likelihood=medium*。修复方向正在被实际用户验证有效（接近无 cache-aware 的基线），但补丁机制与后续收合路径仍需在 cache-aware 系列（见 sched-20260916-011/012/013）里统一推进。*blocking_issues*：无新增。*next_action*：Intel 侧确认补丁机制并把改动收敛进 cache-aware 系列提交。

## 效果评估
Klaus 实测：两个构建测试「几乎同速」于无 cache-aware 内核，约比早期 cache-aware 内核快 2%；核心柱状图无错放进程。属用户实测，非量化基准。

## 我可以参与的点
- kind=testing：在同类 AMD big/little 平台复测构建类负载，确认 cache-aware 与无 cache-aware 内核的性能差距是否闭合。
- kind=discussion：结合 107581 的反馈，评估「动态禁用大小核上的 cache-aware」与「修复容量/选核逻辑」两条路线的取舍。

## 参考链接
- Klaus 反馈：https://lore.kernel.org/all/8aea0f25-0317-42ac-b59f-1a008c6eb106@computerix.info/
