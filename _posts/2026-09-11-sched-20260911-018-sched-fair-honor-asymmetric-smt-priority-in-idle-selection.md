---
id: sched-20260911-018
subject: 'sched/fair: Honor asymmetric SMT priority in idle selection'
date: '2026-09-11'
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <20260909062649.469633-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/1529268b-8e10-4fef-be6e-60b6dd1e74a0@arm.com/
authors:
- Andrea Righi
maintainers_involved:
- Vincent Guittot
- Dietmar Eggemann
current_version: v4
patch_series:
- version: v4
  msgid: <20260909062649.469633-1-arighi@nvidia.com>
  date: 2026-09-09
  summary: 2 补丁：慢路径同样遵守 sibling 优先级，helper 定名 select_idle_smt_cpu()。
  review_outcome: 09-11 Dietmar：for_each_domain() 应换成 rcu_dereference_all(cpu_rq(cpu)->sd)；static
    key 替换与 drop 波及问题承前未解。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v6 未发出（static key 替换 + 域遍历修改待落）
  - Olympus 系列被 PeterZ drop 的连带影响（承 sched-20260910-008）
  next_action: v6 一并落实 sched_smt_active() 与取域修改，再请 PeterZ 重新收取
contribution_opportunities:
- kind: review
  description: 核对 v6 的取域与 RCU 边界；跟进 sched_smt_active() 下无 ASYM_PACKING 平台的无谓扫描问题
generated_at: '2026-09-14T11:35:00'
source_email_count: 1
related_articles:
- sched-20260910-008
- sched-20260910-007
tags:
- arm64
- topology
- idle
- hyperthreading
title: 'sched/fair: Honor asymmetric SMT priority in idle selection'
layout: article
---

## TL;DR
Andrea Righi 让 idle 选核遵守非对称 SMT 优先级的系列当日收到 Dietmar Eggemann 的一条实现级意见：select_idle_smt_cpu() 里的 for_each_domain() 建议换成 `sd = rcu_dereference_all(cpu_rq(cpu)->sd)`。改动很小，但指向该 helper 在 RCU/域遍历上的实现规范；系列的主体争议（static key 替换、MIDR 检测机制、PeterZ drop）承 sched-20260910-008 不变。

## 背景与问题
系列 v4（2 补丁）让慢路径同样遵守 sibling 优先级，helper 定名 select_idle_smt_cpu()。09-10 已确认将移除 static key、改用 sched_smt_active()，并因 Olympus 系列被 PeterZ drop 而连带承压（详见 sched-20260910-008、sched-20260911-017）。

## 技术方案
Dietmar 的意见针对 select_idle_smt_cpu() 的域遍历实现：不用 for_each_domain()（宏会引入对 per-CPU 域链表的隐式遍历方式），而是直接取 `sd = rcu_dereference_all(cpu_rq(cpu)->sd)`——在持锁/RCU 语义上更显式。该 helper 的功能定位（在 SMT 域内按优先级挑 idle sibling）承 v4 不变，当日无新代码。

## 版本演进与当前进展
current_version: v4（v4 cover msgid `<20260909062649.469633-1-arighi@nvidia.com>`；当日缓存仅 Dietmar 对 2/2 的回帖一封）。

- v4（09-08/09）：慢路径遵守 sibling 优先级、helper 定名（承 sched-20260910-008）；
- 09-10：Andrea 确认移除 static key、改 sched_smt_active()，将落入下一版（与 v5 线程合流为 v6）；
- 09-11（本文窗口）：Dietmar 的域遍历实现意见。

## Maintainer 意见与讨论焦点
- **Dietmar Eggemann**：select_idle_smt_cpu() 应显式取 rq->sd 而非 for_each_domain()；
- 承前未解：Vincent 的 static key 质疑已由作者接受但未落版；PeterZ drop 系列的连带影响未消除。当日无新分歧。

## 合入评估
likelihood=medium（维持 sched-20260910-008 的评估）：技术路线未被否定、作者积极整改，但 v6 未发出且 arm64 检测机制（连带自 sched-20260911-017）未决。blocking_issues：v6 未发出（static key 替换 + Dietmar 的域遍历意见都要落进去）；sched-20260910-007 的 drop 波及本系列。next_action：v6 中一并落实 sched_smt_active() 替换与 rcu_dereference_all 取域，再请 PeterZ 重新收取。

## 效果评估
无新效果数据：本日仅实现规范讨论。承 sched-20260910-008：系列收益数据限于作者的 Olympus 平台陈述。

## 我可以参与的点
- kind=review：v6 发出后核对 select_idle_smt_cpu() 的取域方式（rcu_dereference_all(cpu_rq(cpu)->sd)）与 RCU 临界区边界，并跟进此前提出的开放问题——sched_smt_active() 为真但无 SD_ASYM_PACKING 排序的平台会不会付出无谓扫描（承 sched-20260910-008，v6 发出前无人回答）。

## 参考链接
- Dietmar 的回帖：https://lore.kernel.org/all/1529268b-8e10-4fef-be6e-60b6dd1e74a0@arm.com/
- v4 cover（msgid 取自回帖 References）：https://lore.kernel.org/all/20260909062649.469633-1-arighi@nvidia.com/
- v4 2/2：https://lore.kernel.org/all/20260909062649.469633-3-arighi@nvidia.com/
