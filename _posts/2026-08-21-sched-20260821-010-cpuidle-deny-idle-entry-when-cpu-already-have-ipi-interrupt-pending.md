---
id: sched-20260821-010
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: 未获取到
lore_url: 未获取到
authors:
- Maulik Shah
maintainers_involved:
- Daniel Lezcano
- Sudeep Holla
current_version: v2
patch_series:
- version: v2
  msgid: 未获取到
  date: 2026-08-21
  summary: 在 cpuidle_enter_state() 中检查 IPI pending 阻止 idle 进入
  review_outcome: Daniel Lezcano 认为应在 idle loop 层面处理
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Daniel Lezcano 认为方案位置不对，应在 idle loop 而非 cpuidle
  next_action: 重新定位到 idle loop 或提供更强理由
contribution_opportunities:
- kind: discussion
  description: 提供 IPI pending 在 idle 路径上的影响数据
generated_at: '2026-08-21T10:00:00'
source_email_count: 4
related_articles: []
tags:
- cpuidle
- ipi
title: 'cpuidle: Deny idle entry when CPU already have IPI interrupt pending'
layout: article
---

## TL;DR

v2 补丁尝试在 CPU 已有 IPI 中断挂起时阻止进入 idle 状态，但 Daniel Lezcano 认为这应该在 idle loop 而非 cpuidle 框架中处理，Maulik Shah 的 v2 方案方向受到质疑。

## 背景与问题

当 CPU 有挂起的 IPI 中断时，进入 idle 状态可能导致中断延迟。该补丁尝试在 `cpuidle_enter_state()` 中增加检查，在检测到 IPI 挂起时阻止 idle 进入。

## 技术方案

v2 在 cpuidle 框架中增加 IPI pending 检查。Daniel Lezcano (Qualcomm) 认为这应该在 idle loop 层面处理，而不是在 cpuidle 子系统中特殊处理。

## 版本演进与当前进展

- **v2** 讨论中：Daniel Lezcano 建议 "this should be handled directly in the idle loop and not in cpuidle_enter_state()"
- Maulik Shah 回应说 idle entry 不会发生时 stats 也不需要更新
- Sudeep Holla (ARM) 建议设置 `last_residency_ns == 0`，类似 `need_resched()` 路径

## Maintainer 意见与讨论焦点

**分歧**：Daniel Lezcano 不认为 cpuidle 应该特殊处理 IPI pending，认为这属于 idle loop 的职责。这可能导致方案需要重新定位。

## 合入评估

- **likelihood**: low
- **blocking_issues**: Daniel Lezcano 认为方案位置不对
- **next_action**: 需要在 idle loop 层面重新实现，或说服维护者 cpuidle 层处理更合适

## 效果评估

暂无数据。

## 我可以参与的点

- 分析 IPI pending 在 idle 路径上的实际影响，提供数据支持讨论
- 如果方案移到 idle loop 层面，可以帮助实现

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
