---
id: sched-20260825-010
date: 2026-08-25
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: unknown
lore_url: unknown
authors:
- Hongyan Xia
maintainers_involved:
- Christian Loehle
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需要明确 boost 频率场景下 policy->max 的正确语义
  next_action: 需要 cpufreq 维护者对 boost 频率定义给出意见
contribution_opportunities: []
generated_at: '2026-08-27T10:00:00'
source_email_count: 1
related_articles:
- sched-20260825-009
tags:
- cpufreq
- cfs
title: 'sched/fair: Only apply cpufreq pressure where frequency is invariant'
layout: article
---

## TL;DR

Hongyan Xia 的 patch 讨论：当 CPU 的频率不变性（frequency invariance）不成立时，不应施加 cpufreq pressure。讨论中澄清了问题本质可能不是频率不变性问题，而是 boost 频率与 `policy->max`/`cpuinfo.max_freq` 的定义差异导致误判。

## 背景与问题

CFS 在检测到 cpufreq 压力时会调整负载均衡行为。但如果当前 CPU 的频率本身就不支持频率不变性（如某些 ARM 平台），施加 cpufreq pressure 可能产生错误行为。

Hongyan Xia 的 patch 添加条件检查，只在频率不变性成立的 CPU 上施加 cpufreq pressure。

## 技术方案

在 cpufreq pressure 路径中添加 `arch_scale_freq_invariant()` 检查。

讨论中 Christian Loehle 指出，他的系统上 `cpuinfo.max_freq` 包含 boost 频率而 `policy->max` 不包含，导致 `policy->max < cpuinfo.max_freq` 的比较给出了虚假的"压力"信号。Hongyan 回应说这不是频率不变性问题，而是 boost 频率定义的问题。

## 版本演进与当前进展

讨论阶段。Hongyan Xia 和 Christian Loehle 对问题本质有不同理解：
- Hongyan：认为是频率不变性条件缺失
- Christian：认为是 boost 频率与 policy->max 的定义差异

## Maintainer 意见与讨论焦点

- **Hongyan Xia**：指出 Christian 的系统上 boost 频率定义差异导致的误判不是频率不变性问题，建议让经常处理 boost 频率的人来评论
- **Christian Loehle**：认为 hold_freq 和 blocked utilization 是独立问题

## 合入评估

- **likelihood: medium** — 方向合理但需要澄清问题定义
- **blocking_issues**: 需要明确 boost 频率场景下 policy->max 的正确语义
- **next_action**: 需要 cpufreq 维护者对 boost 频率定义给出意见

## 效果评估

暂无效果数据。

## 我可以参与的点

- 如果手上有 ARM 平台（特别是支持 boost 频率的），可以测试并回帖说明 `policy->max` vs `cpuinfo.max_freq` 的实际行为

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
