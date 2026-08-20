---
subject: 'intel_idle: Avoid using deep idle states during initialization'
id: sched-20260804-022
date: 2026-08-04
subsystem: idle
type: fix
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Zhang Rui
maintainers_involved:
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-04
  summary: intel_idle 在初始化/early 阶段若选到 deep idle 状态，可能在某些平台导致唤醒延迟异常或初始化时序问题；改为在初始化期间避免
    deep idle，待初始化完成后再允许。
  review_outcome: v1 刚发，邮件未显示 NAK。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需确认哪些平台受影响、避免 deep idle 的窗口是否过宽
  next_action: 等待 Rafael 对平台适用性与窗口边界的认可。
contribution_opportunities:
- kind: testing
  description: 可在受影响平台（特定 Intel 型号）上验证初始化期间避免 deep idle 后唤醒延迟/初始化稳定性是否改善，回帖数据。
generated_at: '2026-08-05T00:25:00'
source_email_count: 1
related_articles: []
tags:
- idle
- intel_idle
- latency
title: 'intel_idle: Avoid using deep idle states during initialization'
layout: article
---

# intel_idle: 初始化期间避免 deep idle

## TL;DR
intel_idle 在初始化/early 阶段若进入 deep idle 状态，可能在某些平台引起唤醒延迟异常或初始化时序问题。Zhang Rui 改为初始化期间避免 deep idle，完成后再允许。低严重度修复，合入可能性 medium，待平台确认。

## 背景与问题
intel_idle 驱动在 early/初始化阶段就可能选到 deep C-state。在某些平台上，该阶段进入 deep idle 会与尚未完成的初始化时序冲突，或导致异常高的唤醒延迟，影响启动稳定性。

## 技术方案
在初始化完成前限制可用的 idle 状态深度（避免 deep idle），初始化完成后再放开。改动集中在 intel_idle 的 early 初始化路径与状态可用性判断。

## 版本演进与当前进展
v1（2026-08-04），作者 Zhang Rui。

## Maintainer 意见与讨论焦点
尚未见 Rafael 回复。焦点在平台适用性与「避免 deep idle 的窗口」是否过宽（过宽会削弱初始化期节能）。

## 合入评估
合入可能性 medium。平台相关修复，需确认适用边界。

## 效果评估
无基准；属启动稳定性/延迟修复，需受影响平台实测。

## 我可以参与的点
- 在受影响 Intel 型号上验证初始化期避免 deep idle 后唤醒延迟/启动稳定性是否改善，回帖数据。

## 参考链接
- lore thread: 未获取到
