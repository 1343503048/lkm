---
subject: 'sched/topology: Add a cpus_read_lock to rebuild_sched_domains()'
id: sched-20260814-003
date: 2026-08-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260814224515.sd_shared@prateek>
lore_url: 未获取到
authors:
- K Prateek Nayak
- Valentin Schneider
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- Dietmar Eggemann
current_version: v1
patch_series:
- version: v1
  msgid: <20260814224515.sd_shared@prateek>
  date: 2026-08-14
  summary: 修复 sched/topology 在 sd_llc 与 sd_asym_cpucapacity 指向同一域时，init_sched_domain_shared()
    重复覆盖并泄漏 sd->shared 的 kmemleak（Breno 报告）。同时涉及 NUMA masks 释放、rebuild_sched_domains
    加 cpus_read_lock、Do-not-override sd->shared 等关联修复。
  review_outcome: Prateek 在 8/14 晚追加 ping，建议进 sched/urgent（内存泄漏），否则 AUTOSEL 兜底稳定分支；Valentin
    参与其它 topology 修复讨论。
upstream_commit: null
fixes_commit: 9e005ed21152d
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Peter 接受进 sched/urgent（泄漏修复），或 AUTOSEL 进稳定分支。
contribution_opportunities:
- kind: review
  description: 评审 init_sched_domain_shared() 提前返回对退化路径 refcount 的影响。
- kind: testing
  description: 在单 LLC 的非对称系统上跑 kmemleak 验证 sd->shared 不再泄漏。
generated_at: '2026-08-15T00:15:00'
source_email_count: 4
related_articles: []
tags:
- topology
- sched/core
title: 'sched/topology: Add a cpus_read_lock to rebuild_sched_domains()'
layout: article
---

## TL;DR
K Prateek Nayak（Valentin Schneider 等参与）修复 sched/topology 的 `sd->shared` 重复分配/泄漏：当 `sd_llc` 与 `sd_asym_cpucapacity` 指向同一域时，`init_sched_domain_shared()` 会覆盖并泄漏先前分配。同时涉及 NUMA masks 释放、rebuild 加锁等关联修复。属内存泄漏修复，合入可能性 high。

## 背景与问题
commit `9e005ed21152d`（"sched/topology: Allow multiple domains to claim sched_domain_shared"）无条件为 `sd_llc` 分配 `sd->shared`。在非对称单 LLC 系统上，`sd_llc` 与 `sd_asym_cpucapacity` 指向同一域时，`init_sched_domain_shared()` 会重复覆盖 `sd->shared`，导致前一个分配泄漏（Breno 的 kmemleak 报告）。

## 技术方案
- 在 `init_sched_domain_shared()` 开头：若 `sd->shared` 已有效赋值则提前返回（该分配在各域级别只应计一次，退化路径只减一次 refcount，语义正确）。
- 附带修正一处拼写（avaialable→available）。
- 关联讨论中的其它 topology 修复：NUMA masks 在分配失败路径释放、rebuild_sched_domains()/partition_sched_domains() 加 `cpus_read_lock` 防并发重建、Do-not-override sd->shared 分配。

## 版本演进与当前进展
当前 v1（Prateek 主修复）。8/14 晚 Prateek 追加 ping，建议进 sched/urgent；若不稳定分支，AUTOSEL 兜底，否则手动发 Greg 进 v7.2。

## Maintainer 意见与讨论焦点
焦点：泄漏修复是否进 sched/urgent（正确，属回归）；与 Valentin 的其它 topology 修复是否合为一批。

## 合入评估
合入可能性 high。明确的内存泄漏回归修复，已被测试者（Breno、Dietmar）Tested-by。

## 效果评估
修复 kmemleak 泄漏；Breno、Dietmar 已 Tested-by。

## 我可以参与的点
- 在单 LLC 非对称系统验证泄漏消失；
- 评审提前返回对退化路径 refcount 的正确性。

## 参考链接
- lore: 未获取到
- Fixes: 9e005ed21152d
- Reported-by: Breno Leitao
