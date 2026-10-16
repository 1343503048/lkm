---
id: sched-20261016-005
date: 2026-10-16
subject: 'sched/cache: Avoid publishing partial LLC utilization'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261016032759.45279-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261016032759.45279-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v3
patch_series:
- version: v3
  msgid: <20261016032759.45279-1-jemmywong512@gmail.com>
  date: 2026-10-16
  summary: '无功能变化，补注释 + Cc: stable # 7.2.x + 收 Tim Chen/Chen Yu R-B'
  review_outcome: 当日被 Peter 合入 tip sched/core
upstream_commit: fcceb7da9465
fixes_commit: f025ef275388
merged_branch: sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 无（已合入）；关注 7.2.x stable 回合
contribution_opportunities: []
generated_at: '2026-10-17T01:30:00'
source_email_count: 3
related_articles:
- sched-20261010-004
- sched-20261013-011
- sched-20261014-009
- sched-20261015-018
tags:
- cfs
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>：Jemmy Wong 修 cache-aware 调度「部分 LLC 利用率」问题——`record_sg_llc_stats()` 把「部分利用率 + 完整容量」一起发布，`can_migrate_llc()` 误判忙碌 preferred LLC 有空余。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-011-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261013-011</a>：Jemmy 发 v2（`LBF_ALL_PINNED || !cpumask_subset` 折中），Tim Chen 确认方向。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-009-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261014-009</a>：Tim Chen 与 Chen Yu 双双 Reviewed-by；Tim 表示「也是 7.2.x stable 候选」；Chen Yu 建议补 `LBF_ALL_PINNED` 语义注释。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-018-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261015-018</a>：Jemmy 询问是否应发 v3（stable 标注 + 注释 + tags）。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-005-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261016-005</a>（今天）：Jemmy 发 v3（无功能变化，补 Chen Yu 建议的注释、`Cc: stable # 7.2.x`、收 Tim Chen/Chen Yu 的 R-B），**同日被 Peter 合入 tip sched/core（commit fcceb7da9465）**。

## 背景与问题
（承接 20261010-004 → 20261015-018）负载均衡因 all-pinned redo、或 CPU hotplug 使 `env->cpus` 与 `sched_group_span(group)` 不一致时，把只覆盖部分 CPU 的利用率当整组利用率发布，`can_migrate_llc()` 误判忙碌 preferred LLC 为有富余，导致任务过度聚合、争用与时延加剧（作者标注「Found by inspection」）。

## 技术方案
（承接 v2）`record_sg_llc_stats()` 在 affinity retry（`LBF_ALL_PINNED`）时跳过发布、保留首轮快照，且首轮只在 `env->cpus` 覆盖整组时发布共享 LLC 统计；负载均衡仍使用按 affinity 过滤后的统计。v3 无功能变化，仅补注释与 stable 标注。

## 版本演进与当前进展
- v3（2026-10-16，<20261016032759.45279-1-jemmywong512@gmail.com>）：相对 v2 无功能变化，补 `LBF_ALL_PINNED` 语义注释、`Cc: stable@vger.kernel.org # 7.2.x`、收 Tim Chen/Chen Yu 的 R-B。
- 当天 Peter 合入 tip sched/core：`fcceb7da9465`。

## Maintainer 意见与讨论焦点
Tim Chen（Intel）、Chen Yu（Intel）双双 Reviewed-by 并建议补注释 + stable 标注；Prateek、Tim 为 Suggested-by。无 NAK，方向一致。

## 合入评估
*likelihood=merged*。已合入 tip sched/core（commit `fcceb7da9465`）。*blocking_issues*：无。*next_action*：无（已合入）；关注 7.2.x stable 回合。

## 效果评估
无量化数据（作者自述 code inspection 发现）。

## 我可以参与的点
当前阶段已合入，无明显参与空间；可持续关注 7.2.x stable 回合。

## 参考链接
- tip 合入通知：https://lore.kernel.org/all/179213767625.2666988.4719847157551221636.tip-bot2@tip-bot2/
- v3 patch：https://lore.kernel.org/all/20261016032759.45279-1-jemmywong512@gmail.com/
