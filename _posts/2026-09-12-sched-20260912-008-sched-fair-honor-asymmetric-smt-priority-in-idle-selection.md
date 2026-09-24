---
id: sched-20260912-008
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
date: '2026-09-12'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260909062649.469633-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/aqSB-zn9_ji_Ekc8@gpd4/
authors:
- Andrea Righi
maintainers_involved:
- Dietmar Eggemann
current_version: v4
patch_series:
- version: v4
  msgid: <20260909062649.469633-1-arighi@nvidia.com>
  date: 2026-09-09
  summary: 慢路径 idle 选核遵守非对称 SMT 优先级，helper 定名 select_idle_smt_cpu()。
  review_outcome: 09-12 Andrea 确认 Dietmar 的最低域直取意见已本地落实，待落入 v6（连同 sched_smt_active()
    替换 static key）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v6 未发出
  - Olympus 系列被 drop 的连带影响（承 sched-20260910-008）
  next_action: v6 落实三项修改后请 PeterZ 重新收取
contribution_opportunities:
- kind: review
  description: v6 发出后核对 static key 替换、最低域直取与无 ASYM_PACKING 平台门控
generated_at: '2026-09-14T12:40:00'
source_email_count: 1
related_articles:
- sched-20260911-018
- sched-20260910-008
tags:
- arm64
- topology
- idle
- hyperthreading
title: 'sched/fair: Honor asymmetric SMT priority in idle selection'
layout: article
---

## TL;DR
Andrea Righi 当日确认 Dietmar Eggemann 09-11 的实现意见已就地落实：select_idle_smt_cpu() 改为直接取最低调度域（rcu_dereference_all(cpu_rq(cpu)->sd)），将随下一版发出。系列其余状态（v6 待发、Olympus 系列被 drop 的连带影响）不变。本文为增量更新，v4 分析见 sched-20260911-018。

## 背景与问题
（承 sched-20260911-018）系列让慢路径 idle 选核遵守非对称 SMT 优先级，helper 为 select_idle_smt_cpu()；Dietmar 指出其中的 for_each_domain() 应改为显式 `sd = rcu_dereference_all(cpu_rq(cpu)->sd)` 取最低域。

## 技术方案
本日无新代码。Andrea 回复确认实现方向：「Correct, I've changed it locally already to inspect the lowest scheduling domain directly.」——即取最低调度域的改法已在本地完成，待落入下一版（v6，连同 sched_smt_active() 替换 static key）。

## 版本演进与当前进展
*current_version: v4（v4 cover msgid `<20260909062649.469633-1-arighi@nvidia.com>`；当日缓存仅 Andrea 的确认回帖一封）*。

- v4（09-08/09）→ 09-10 static key 移除决定 → 09-11 Dietmar 取域意见 → 09-12 Andrea 确认已改、待发 v6。

## Maintainer 意见与讨论焦点
- **Dietmar Eggemann**（承 09-11）：取域方式意见被完全接受；
- 未解事项不变：v6 未发出；sched-20260910-007 的 Olympus 系列被 PeterZ drop 的连带影响仍在；「sched_smt_active() 为真但无 SD_ASYM_PACKING 平台的无谓扫描」问题（09-10-008 提出）仍无人回答。

## 合入评估
*likelihood=medium*（不变）：评审意见收敛、作者响应积极，但 v6 未发出前无新信息改变评估。blocking_issues 与 next_action 均承 sched-20260911-018：v6 一并落实 static key 替换与取域修改后再请 PeterZ 重新收取。

## 效果评估
无新效果数据（承前：收益数据限于作者的 Olympus 平台陈述）。

## 我可以参与的点
- kind=review：v6 发出后一次性核对三项——sched_smt_active() 替换、最低域直取（rcu_dereference_all）、以及无 ASYM_PACKING 排序平台的开销问题是否在实现中被门控。

## 参考链接
- Andrea 的确认回帖：https://lore.kernel.org/all/aqSB-zn9_ji_Ekc8@gpd4/
- Dietmar 的原始意见：https://lore.kernel.org/all/1529268b-8e10-4fef-be6e-60b6dd1e74a0@arm.com/
- v4 cover：https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/
