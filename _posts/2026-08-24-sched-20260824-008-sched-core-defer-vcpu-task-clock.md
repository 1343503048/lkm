---
id: sched-20260824-008
date: 2026-08-24
subsystem: sched
type: feature
status: rfc
severity: low
thread_root_msgid: <unknown>
lore_url: 未获取到
authors:
- Dongli Zhang
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: 2026-08-24
  summary: 'RFC: 延迟被抢占远程 vCPU 的 clock_task 更新'
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - RFC 阶段，需要社区反馈
  next_action: 等待调度器和 KVM 维护者回复
contribution_opportunities:
- kind: testing
  description: 在 KVM 环境中测试调度记账修复效果
generated_at: '2026-08-25T10:40:00'
source_email_count: 2
related_articles: []
tags:
- sched/core
- virtualization
title: 'sched/core: Defer preempted remote vCPU task clock updates'
layout: article
---

## TL;DR
KVM 客户机中，当 vCPU A 为被抢占的 vCPU B 做记账时，由于 KVM host 直到 vCPU B 重新进入才更新 stealtime，导致 vCPU A 无法观察到 steal 时间，错误地将 stolen 区间计入任务运行时间。RFC 提出延迟远程 CPU 对已标记为 preempted 的 vCPU 的 `clock_task` 更新。

## 背景与问题
Linux 调度器允许一个 CPU 通过 `update_rq_clock_task()` 为另一个 CPU 做记账。在裸机上这工作正常，但在 KVM 客户机中存在问题：

假设 vCPU A 为 vCPU B 做记账，而 vCPU B 被 KVM host 抢占了 10 秒。KVM host 直到 vCPU B 即将重新进入客户机时才更新 stealtime。因此，vCPU A 无法观察到 vCPU B 的 stealtime 增加。

结果：客户机内核错误地认为在 vCPU B 上运行的任务独占使用了 vCPU 很长时间，该任务因此可能被施加额外的调度惩罚。

## 技术方案
两个补丁的 RFC 系列：
1. **Patch 1/2**（cover letter）：描述问题和修复思路
2. **Patch 2/2**：在 `kernel/sched/core.c` 中，当远程 CPU 尝试更新一个已被标记为 `preempted` 的 vCPU 的 `clock_task` 时，延迟该更新。将延迟的增量折叠到下一次可以正常进行的更新中，使 IRQ 和 steal 记账一起处理。

关键约束：需要 hypervisor 在清除 `preempted` 标记之前发布最新的 stealtime。

## 版本演进与当前进展
- **RFC v1**（Dongli Zhang）：首发，标注 `Assisted-by: Codex:GPT-5.5`

当前版本：RFC，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者回复。该补丁涉及调度器核心记账逻辑和 KVM 交互，需要 Peter Zijlstra 和 KVM 维护者共同确认。

## 合入评估
合入可能性 **low**（RFC 阶段）：
- 问题真实但场景特定（KVM 客户机 + 远程记账）
- 方案涉及调度器核心路径，需要仔细审查
- `blocking_issues`：需要确认延迟更新不会引入其他问题
- `next_action`：等待社区反馈，可能需要更多测试数据

## 效果评估
暂无性能数据。理论上可以修复 KVM 客户机中被抢占任务的错误调度惩罚，但需要实际测试验证。

## 我可以参与的点
- 如果有 KVM 虚拟化环境，可以帮忙测试该 RFC 是否确实修复了调度记账问题
- 可以帮忙分析延迟 `clock_task` 更新是否会影响其他调度决策

## 参考链接
- lore thread: 未获取到
