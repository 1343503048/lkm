---
id: sched-20260825-009
date: 2026-08-25
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: unknown
lore_url: unknown
authors:
- Christian Loehle
- Hongyan Xia
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Sashiko 报告的并发问题需先解决
  next_action: Christian 发出 hold_freq 的 RFC patch
contribution_opportunities:
- kind: discussion
  description: 参与讨论预测唤醒后利用率以驱动 idle 前最后一次调频的方案可行性
generated_at: '2026-08-27T10:00:00'
source_email_count: 2
related_articles: []
tags:
- cpufreq
- nohz
title: 'sched/cpufreq: Reevaluate frequency before tickless idle'
layout: article
---

## TL;DR

关于 schedutil 在 CPU 进入 tickless idle 前是否应该最后一次重新评估频率的讨论。Christian Loehle 正在开发一个基于 irq_work 的方案来处理 `sugov_hold_freq()` 场景，Hongyan Xia 表示 LGTM 但指出 Sashiko 报告的并发问题需要先解决。核心争议：hold_freq 和 blocked utilization 是两个独立问题但可能有相似的解决方案。

## 背景与问题

当前 schedutil 在 CPU 进入 tickless idle 后可能保持较高频率（`sugov_hold_freq()`），直到下一个 tick 才降低。这导致：
- CPU 在 idle 期间仍然以高频运行，浪费能耗
- 特别是在 shared frequency 域中，一个 idle CPU 的高频会拖累整个域

理想行为是在进入 idle 前最后一次评估频率，基于唤醒后的预期利用率。

## 技术方案

Christian Loehle 的方案思路：
- 使用 `irq_work` 在下一个 tick 时检查是否需要降低 hold_freq
- 如果 `sugov_hold_freq()` 持续了一个 tick  duration 没有新更新，则清除 hold_freq
- 缺点：会延迟一个 tick 的 tick-stop

Christian 认为 hold_freq 和 blocked utilization 是独立问题，但解决方案可能类似。他计划先发 hold_freq 的 RFC。

Hongyan Xia 提出更通用的想法：预测唤醒后的利用率并据此在 idle 前最后一次调频，但承认"predictions are hard"。

## 版本演进与当前进展

讨论阶段，尚无正式 patch。Christian 正在测试 irq_work 方案，计划发 RFC。

## Maintainer 意见与讨论焦点

- **Hongyan Xia**：LGTM（对 Christian 的方向），但指出 Sashiko 报告的并发问题需要先解决。认为 hold_freq 是"clearly wrong behavior"
- **Christian Loehle**：正在开发 irq_work 方案，承认不是理想方案但是目前能想到的最好方法。PREEMPT_RT 场景使问题更复杂

## 合入评估

- **likelihood: unknown** — 仍在讨论/开发阶段
- **blocking_issues**: Sashiko 报告的并发问题需要先解决
- **next_action**: Christian 发出 hold_freq 的 RFC patch

## 效果评估

暂无效果数据。Christian 认为 hold_freq 是"clearly wrong behavior"（主观判断，未见测试数据）。

## 我可以参与的点

- 当前处于 RFC 前讨论阶段，可以参与讨论预测唤醒后利用率的方案可行性
- 后续 Christian 发出 RFC 后，可以在特定硬件上测试 irq_work 方案的能耗影响

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
