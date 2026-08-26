# cpuidle: Deny idle entry when CPU already have IPI interrupt pending

## TL;DR

Maulik Shah（Qualcomm）的 v2 讨论：当 CPU 已有 IPI 中断挂起时，应拒绝进入 idle 状态，避免延迟响应。提供了详细的 LeMans SoC（8 CPU）上的 trace 数据，展示 menu governor 在 `get_typical_interval()` 循环中收到 IPI 但仍预测深度 idle 的时序。

## 背景与问题

在 ARM SoC（Qualcomm LeMans）上，GLMark2 负载下观察到以下场景：
1. CPU7 进入 idle，menu governor 正在 `menu_select()` 中分析历史样本
2. CPU6 发送 IPI 到 CPU7（wake-up 事件）
3. CPU7 的 menu governor 仍在 `get_typical_interval()` 循环中处理历史数据
4. IPI 已挂起但 menu governor 仍预测深度 idle 状态
5. CPU 进入 idle 后需要额外延迟处理挂起的 IPI

关键时序（来自 trace）：
- 791.122084: CPU7 在 `menu_select()` 分析 8 个历史样本
- 791.122087: CPU6 发送 IPI 到 CPU7
- CPU7 仍在 idle prediction 循环中，未检查 IPI 挂起状态

## 技术方案

在 cpuidle 入口路径添加 IPI 挂起检查：如果 CPU 已有 pending IPI，拒绝 idle 入口，直接返回处理中断。

v2 的具体实现细节未在缓存邮件中完整展示。

## 版本演进与当前进展

v2 讨论阶段。Maulik Shah 提供了详细的 trace 数据支持修复的必要性。

## Maintainer 意见与讨论焦点

- **Maulik Shah** 提供了 LeMans SoC 上的详细 trace，展示问题场景
- 讨论中涉及 menu governor 的预测逻辑与实际中断到达的时序问题

## 合入评估

- **likelihood: medium** — 问题明确，但 cpuidle 入口路径的额外检查需要评估对正常路径的性能影响
- **blocking_issues**: 无
- **next_action**: 等待 cpuidle maintainer review

## 效果评估

作者提供了详细的 trace 数据，展示 IPI 挂起后仍进入 idle 的延迟问题。具体延迟数字未在缓存邮件中给出。

## 我可以参与的点

- **在 ARM 平台测试**：如果有 Qualcomm 或类似 ARM SoC，可以复现并测量 IPI 挂起场景下的 idle 延迟
- 当前阶段可以参与讨论 idle 入口检查的最佳位置（menu_select 内部 vs cpuidle 入口框架层）

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到

---
id: sched-20260825-012
date: 2026-08-25
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: "unknown"
lore_url: "unknown"
authors: [Maulik Shah]
maintainers_involved: []
current_version: v2
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等待 cpuidle maintainer review v2"
contribution_opportunities:
  - kind: testing
    description: "在 ARM SoC 平台复现 IPI 挂起场景下的 idle 延迟并测量"
  - kind: discussion
    description: "参与讨论 idle 入口 IPI 检查的最佳位置"
generated_at: "2026-08-27T10:00:00"
source_email_count: 1
related_articles: []
tags: [idle, arm64]
---
