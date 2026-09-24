---
id: sched-20260914-007
date: '2026-09-14'
subject: 'sched/fair: avoid creating misfits during cache-aware balancing'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260825174112.2580942-1-tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/20260914025949.1348528-1-kobak@nvidia.com/
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
  blocking_issues:
  - 无合入卡点；复现方法待 Tim 补充
  next_action: 等 Tim 公开测试方法；NVIDIA 平台复现验证修复通用性
contribution_opportunities:
- kind: discussion
  description: 在混合架构平台按 cover 描述复现 misfit 并回帖观测方法，补第三方验证
generated_at: '2026-09-15T09:30:00'
source_email_count: 1
related_articles:
- sched-20260904-006
tags:
- load_balance
- topology
title: 'sched/fair: avoid creating misfits during cache-aware balancing'
layout: article
---

## TL;DR
增量更新，全貌见 sched-20260904-006（该修复已合入 tip `sched/urgent`，commit `f0d243a96f2684ad771d678767d17972cf840bd7`）。09-14 NVIDIA KobaK 向作者 Tim Chen 提方法学问题：cover 解释了失败模式，但未说明观测方法，希望公开复现细节（hybrid 代际、workload、是否用 schedstat lb_imbalance_misfit 或其他信号）。Tim 尚未回复。

## 背景与问题
承 sched-20260904-006：混合架构（SD_ASYM_CPUCAPACITY）上 cache-aware balancing 为了追 preferred LLC 把任务拉到装不下它的目标 CPU、人为制造 misfit；修复同时把 misfit 迁移优先级提到 LLC 聚合之上，已进 tip。今日为合入后的复现方法讨论——NVIDIA 侧想在自家平台复现并验证。

## 技术方案
无新代码。今日是测试方法学的讨论：KobaK 承认 cover 描述的 LLC locality vs capacity loss 取舍清晰，但指出 "I did not find a note on the observation method"，请 Tim 分享测试与观测方式。

## 版本演进与当前进展
- 08-25：Tim Chen 单补丁发出；09-04 前进 tip（sched-20260904-006）。
- 09-14（本文窗口）：KobaK 提复现方法问题，无新版本发出。

## Maintainer 意见与讨论焦点
- **KobaK（NVIDIA）**：理解 tradeoff，但求复现方法（hybrid generation、workload、schedstat 信号），以便在 NVIDIA 平台验证。
- **Tim Chen（作者）**：尚未回复。
- 分歧/未闭合处：复现方法未公开，第三方验证悬空。

## 合入评估
*likelihood=merged*（已成事实，承 sched-20260904-006）。*blocking_issues*：无合入卡点；讨论性疑问待 Tim 补充复现方法。*next_action*：等 Tim 公开测试方法；NVIDIA 平台复现验证后可进一步确认修复的通用性。

## 效果评估
无新数据。原 patch 有 0day 在 58 个 config 上构建成功的记录（承 sched-20260904-006）。

## 我可以参与的点
- kind=discussion：如持有混合架构平台，可主动按 cover 描述尝试复现 misfit 并回帖观测方法，帮助社区补齐第三方验证面。

## 参考链接
- KobaK 复现方法提问：https://lore.kernel.org/all/20260914025949.1348528-1-kobak@nvidia.com/
