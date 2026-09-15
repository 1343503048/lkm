---
id: sched-20260915-006
date: '2026-09-15'
subject: 'sched/fair: avoid creating misfits during cache-aware balancing'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260914025949.1348528-1-kobak@nvidia.com>
lore_url: https://lore.kernel.org/all/670e5ffe0964f075ed96e2104d3b25bb4ece5143.camel@linux.intel.com/
authors:
- Tim Chen
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: f0d243a96f2684ad771d678767d17972cf840bd7
fixes_commit: null
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: Ricardo 补充 Nova Lake 测试细节供 NVIDIA 复现验证（已合入，仅补公开复现方法）
contribution_opportunities:
- kind: testing
  description: 在混合 LLC 平台复现 pin LP-E 再 unpin 后任务未迁往强核，并用 mpstat 验证修复后行为
- kind: discussion
  description: 补充 cache-aware 优先于 misfit 迁移在其它混合拓扑上的表现数据
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20260914-007
- sched-20260904-006
tags:
- load_balance
- topology
title: 'sched/fair: avoid creating misfits during cache-aware balancing'
layout: article
---

## TL;DR
本文为增量更新（完整背景见 related_articles，前述修复已合入 tip sched/urgent）。09-15 Tim Chen 回应 NVIDIA KobaK 09-14 的「观测方法」疑问，补上该修复的原始动机场景：Ricardo 在 Nova Lake（LP-E 核独占一个 LLC 域、E/P 核在另一 LLC 域）上把一个多线程进程 pin 到 LP-E 核再 unpin，期望进程迁往更强核却未发生——因为 cache-aware 调度占了优先，可以用 mpstat 直观看到。

## 背景与问题
承 sched-20260914-007：混合架构（SD_ASYM_CPUCAPACITY）上 cache-aware balancing 为追 preferred LLC，把任务拉到装不下它的目标 CPU、人为制造 misfit；修复把 misfit 迁移优先级提到 LLC 聚合之上，已进 tip。09-14 NVIDIA KobaK 希望公开复现细节；09-15 Tim Chen 给出原始动机的实验场景。

## 技术方案
无新代码。Tim Chen 描述动机测试：在 Nova Lake 上（LP-E 核在一个 LLC 域、E/P 核在另一个 LLC 域），把多线程进程 pin 到 LP-E 核再 unpin，预期进程迁往更强核但未发生（cache-aware 调度优先），用 mpstat 即能复现/观测。Tim 表示可将 Ricardo 引入线程做进一步细节讨论。

## 版本演进与当前进展
本日为合入后的动机说明与讨论。该修复已合入 tip（commit 见 related_articles sched-20260914-007），当前处于「补全测试/复现方法学」的收尾沟通，无代码版本变化。

## Maintainer 意见与讨论焦点
- **Tim Chen (Intel)**：补充动机场景（Nova Lake LP-E 测试、mpstat 观测），并主动提出让 Ricardo 提供更多细节。
- **KobaK (NVIDIA)**（09-14）：要求公开复现方法（hybrid 代际、workload、观测信号），本日获回应。
- 无分歧，属复现方法学的信息对齐。

## 合入评估
likelihood=merged。修复已合入 tip sched/urgent（见 related_articles sched-20260914-007）。blocking_issues：无（仅剩复现细节的公开沟通）。next_action：Ricardo/Matt 补充 Nova Lake 测试细节供 NVIDIA 复现验证。

## 效果评估
Tim Chen 描述的行为现象：unpin 后进程未迁往更强核（cache-aware 调度影响），可用 mpstat 观察。为定性行为描述，未给定量化数字；修复是否恢复预期迁移行为需 NVIDIA 侧复现确认。

## 我可以参与的点
- kind=testing：在含 LP-E/E/P 混合 LLC 的平台上（如 Nova Lake 或类似大小核）复现「pin LP-E 再 unpin 后任务未迁往强核」并用 mpstat 验证修复后行为。
- kind=discussion：补充「cache-aware 优先于 misfit 迁移」在其它混合拓扑上的表现数据，帮助评估修复的覆盖面。

## 参考链接
- Tim Chen 回帖：https://lore.kernel.org/all/670e5ffe0964f075ed96e2104d3b25bb4ece5143.camel@linux.intel.com/
- 该修复补丁：https://lore.kernel.org/all/20260914025949.1348528-1-kobak@nvidia.com/
