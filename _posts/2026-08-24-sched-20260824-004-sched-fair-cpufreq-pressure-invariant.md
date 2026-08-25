---
id: sched-20260824-004
date: 2026-08-24
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: 未获取到
authors:
- unknown
maintainers_involved:
- Vincent Guittot
- Hongyan Xia
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-21
  summary: 限制 cpufreq pressure 只在频率不变平台生效
  review_outcome: 被质疑表述不准确
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 原始问题描述被推翻，需重新定位
  next_action: 作者需要重新描述问题根因并发 v2
contribution_opportunities:
- kind: review
  description: 帮忙分析 arch_scale_freq_ref() 在不同架构上的实现
generated_at: '2026-08-25T10:40:00'
source_email_count: 2
related_articles:
- sched-20260821-004
tags:
- sched/fair
- sched/cpufreq
- frequency_invariance
title: 'sched/fair: cpufreq pressure 频率不变性讨论（增量更新）'
layout: article
---

## TL;DR
本文为增量更新，完整背景见 related_articles 中的文章。作者承认原始 commit message 基于频率不变性的解释不正确，实际问题源自 `d2d5c129d07e` 引入的 `cpuinfo.max_freq` fallback 逻辑。讨论仍在继续。

## 版本演进与当前进展
作者在回复中澄清：
> My original commit message did not clearly describe the concrete issue being fixed, and its explanation based on frequency invariance was not correct. After looking into this further, I found that the issue I observed has a different cause: the cpuinfo.max_freq fallback added by d2d5c129d07e.

实际问题：`cpufreq_update_pressure()` 在缺少 `arch_scale_freq_ref()` 时会 fallback 到 `cpuinfo.max_freq`，但这不是真正的最大可持续频率，导致压力计算不准确。

## Maintainer 意见与讨论焦点
- **Vincent Guittot / Hongyan Xia**（之前回复）：质疑"频率不变性"的表述是否准确，要求更具体的问题描述
- **作者回应**：承认表述不当，重新定位问题根因为 `cpuinfo.max_freq` fallback
- **Vincent 追问**：质疑"utilization 超过 capacity"的具体含义——"anything that is always-running without idle time under PELT will reach 1024 eventually regardless of invariance"

分歧点：作者需要更精确地描述问题场景和修复效果，不能依赖"频率不变性"这个宽泛概念。

## 合入评估
合入可能性 **medium**：
- 原始解释被推翻，需要重新定位问题
- 需要更精确的 commit message 和复现数据
- `blocking_issues`：作者需要重新描述问题和修复方案
- `next_action`：作者需要发 v2 重新描述问题，或证明当前方案确实解决了 `cpuinfo.max_freq` fallback 的问题

## 效果评估
暂无效果数据；作者尚未提供具体的性能影响或测试数据。

## 我可以参与的点
- 如果了解 `arch_scale_freq_ref()` 在不同架构上的实现情况，可以帮忙分析哪些平台会触发此问题
- 可以帮忙验证 `cpuinfo.max_freq` fallback 在特定平台上的实际影响

## 参考链接
- lore thread: 未获取到
