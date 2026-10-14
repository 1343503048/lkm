---
id: sched-20261014-009
subject: 'sched/cache: Avoid publishing partial LLC utilization'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261013084338.55100-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20261010113425.34829-1-jemmywong512@gmail.com>
  date: 2026-10-10
  summary: env->cpus 未覆盖整组时跳过发布，保留完整快照
  review_outcome: Prateek 建议 LBF_ALL_PINNED 便宜检查
- version: v2
  msgid: <20261013084338.55100-1-jemmywong512@gmail.com>
  date: 2026-10-13
  summary: LBF_ALL_PINNED || !cpumask_subset 折中，补 Fixes/Suggested-by
  review_outcome: Tim Chen、Chen Yu 双 Reviewed-by；Tim 认为可回 7.2.x stable
upstream_commit: null
fixes_commit: f025ef275388
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 待 SCHED 维护者收取
  - Chen Yu 的注释建议待落地
  next_action: 补注释后由 Peter/Vincent 收取
contribution_opportunities:
- kind: testing
  description: 验证亲和性重试与 hotplug 窗口下 v2 判断行为，核对注释建议准确性
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261010-004
- sched-20261012-007
- sched-20261013-011
tags:
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

> **subject**：sched/cache: Avoid publishing partial LLC utilization

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>：Jemmy Wong 修 cache-aware 调度「部分 LLC 利用率」问题——`record_sg_llc_stats()` 把「部分利用率 + 完整容量」一起发布，`can_migrate_llc()` 误判忙碌 preferred LLC 有空余。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-007-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261012-007</a>：Prateek 建议用更便宜的 `LBF_ALL_PINNED` 替代 `cpumask_subset()`；Jemmy 反驳其语义不匹配。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-011-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261013-011</a>：Jemmy 发 v2（`LBF_ALL_PINNED || !cpumask_subset` 折中），Tim Chen 确认方向。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-009-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261014-009</a>（今天）：**Tim Chen 与 Chen Yu 双双给出 `Reviewed-by`**；Tim 另表示「这也是 7.2.x stable 的候选」；Chen Yu 建议补一段 `LBF_ALL_PINNED` 语义注释。v2 已获 cache-aware 作者群背书，只差 SCHED 维护者收取。

## 背景与问题
（承接 20261010-004 → 20261013-011）负载均衡因 all-pinned redo、或 CPU hotplug 使 `env->cpus` 与 `sched_group_span(group)` 不一致时，把只覆盖部分 CPU 的利用率当整组利用率发布，`can_migrate_llc()` 会误判忙碌的 preferred LLC 为有富余，导致任务过度聚合、争用与时延加剧（作者标注「Found by inspection」）。今日为 v2 的 review 收官。

## 技术方案
（承接 v2）`record_sg_llc_stats()` 开头加 `if ((env->flags & LBF_ALL_PINNED) || !cpumask_subset(sched_group_span(group), env->cpus)) return;`。今日 Chen Yu 建议在该检查处补注释，把 `LBF_ALL_PINNED` 与 redo 的关系讲清：进入 `record_sg_llc_stats()` 时 `LBF_ALL_PINNED` 置位是「处于 redo」的充要条件；redo 时 `env->cpus` 可能残缺，为避免对同一 group 重复计算统计而跳过，影响很小（首轮到 redo 的间隔很短）。

## 版本演进与当前进展
仍为 v2（10-13 发）。今日 Tim Chen（`Reviewed-by` + stable 候选）、Chen Yu（`Reviewed-by` + 注释建议）完成 review，无 v3。

## Maintainer 意见与讨论焦点
- **Tim Chen**（cache-aware 作者）：`Reviewed-by`；并明确「这也是 7.2.x stable 的候选」（修复有回归/正确性价值，可回 stable）。
- **Chen Yu**（cache-aware 共同作者）：`Reviewed-by`；建议补 `LBF_ALL_PINNED` 语义注释。
- 无 NAK；review 已闭环，差注释补充与 SCHED 维护者（Peter/Vincent）收取。

## 合入评估
*likelihood=high*。修复获 cache-aware 作者群（Tim Chen、Chen Yu）双 `Reviewed-by`，且有 stable 候选背书；仅剩补注释与维护者收取。*blocking_issues*：待 SCHED 维护者收取；Chen Yu 的注释建议待落地。*next_action*：作者按 Chen Yu 建议补注释（或说明无需），Peter/Vincent 收取。

## 效果评估
无性能数字；问题为逻辑正确性（「Found by inspection」），修复避免误发布部分利用率。作者未提供复现/压测数据。

## 我可以参与的点
- review/testing：在启用 cache-aware 调度（LLC utilization 记录）的环境下，验证 `LBF_ALL_PINNED || !cpumask_subset` 在亲和性重试与 hotplug 两种窗口下的行为，并核对 Chen Yu 的注释建议是否准确描述了 `LBF_ALL_PINNED` 与 redo 的充要关系。

## 参考链接
- v2 lore：https://lore.kernel.org/all/20261013084338.55100-1-jemmywong512@gmail.com/
- v1 lore：https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
