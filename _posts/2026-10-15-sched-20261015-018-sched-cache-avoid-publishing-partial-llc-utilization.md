---
id: sched-20261015-018
date: 2026-10-15
subject: 'sched/cache: Avoid publishing partial LLC utilization'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261013084338.55100-1-jemmywong512@gmail.com>
lore_url: https://lore.kernel.org/all/20261013084338.55100-1-jemmywong512@gmail.com/
authors:
- Jemmy Wong
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v2
patch_series:
- version: v1
  msgid: null
  date: 2026-10-10
  summary: record_sg_llc_stats() 拒绝发布部分 LLC 利用率
  review_outcome: Prateek 建议 LBF_ALL_PINNED，Jemmy 反驳语义不匹配
- version: v2
  msgid: <20261013084338.55100-1-jemmywong512@gmail.com>
  date: 2026-10-13
  summary: LBF_ALL_PINNED || !cpumask_subset 折中
  review_outcome: Tim Chen、Chen Yu 双 Reviewed-by；建议补注释 + stable 标注
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Jemmy 发 v3（stable 标注 + 注释）后合入
contribution_opportunities: []
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20261010-004
- sched-20261012-007
- sched-20261013-011
- sched-20261014-009
tags:
- cfs
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>：Jemmy Wong 修 cache-aware 调度「部分 LLC 利用率」问题——`record_sg_llc_stats()` 把「部分利用率 + 完整容量」一起发布，`can_migrate_llc()` 误判忙碌 preferred LLC 有空余。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-007-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261012-007</a>：Prateek 建议用更便宜的 `LBF_ALL_PINNED` 替代 `cpumask_subset()`；Jemmy 反驳其语义不匹配。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-011-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261013-011</a>：Jemmy 发 v2（`LBF_ALL_PINNED || !cpumask_subset` 折中），Tim Chen 确认方向。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-009-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261014-009</a>：Tim Chen 与 Chen Yu 双双 `Reviewed-by`；Tim 表示「也是 7.2.x stable 候选」；Chen Yu 建议补 `LBF_ALL_PINNED` 语义注释。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-018-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261015-018</a>（今天）：Jemmy 询问是否应发 v3（带 `Cc: stable@vger.kernel.org # 7.2.x`、补 Chen Yu 建议的注释、附上各 `Reviewed-by`）。

## 背景与问题
（承接 20261010-004 → 20261014-009）负载均衡因 all-pinned redo、或 CPU hotplug 使 `env->cpus` 与 `sched_group_span(group)` 不一致时，把只覆盖部分 CPU 的利用率当整组利用率发布，`can_migrate_llc()` 误判忙碌 preferred LLC 为有富余，导致任务过度聚合、争用与时延加剧（作者标注「Found by inspection」）。

## 技术方案
（承接 v2）`record_sg_llc_stats()` 开头加 `if ((env->flags & LBF_ALL_PINNED) || !cpumask_subset(sched_group_span(group), env->cpus)) return;`。今日无代码变更，是收尾前确认：v3 将补 Chen Yu 建议的 `LBF_ALL_PINNED` 语义注释、附上 Reviewed-by 与 stable 标注。

## 版本演进与当前进展
- v2 已获 Tim Chen、Chen Yu 双 `Reviewed-by`；今日确认 v3 的形式（stable 标注 + 注释 + tags），尚未正式发 v3。

## Maintainer 意见与讨论焦点
Tim Chen（Intel）已 `Reviewed-by` 并明确「7.2.x stable 候选」；Chen Yu 建议补注释并 `Reviewed-by`。无 NAK，方向一致，只剩 v3 的收尾确认。

## 合入评估
*likelihood=high*。双维护者 Reviewed-by，仅差 v3 形式化与 stable 标注确认。*blocking_issues*：无实质阻塞。*next_action*：Jemmy 发 v3（stable 标注 + 注释）后合入。

## 效果评估
无量化数据（作者自述 code inspection 发现）。

## 我可以参与的点
当前阶段暂无明显参与空间，已获双维护者 Reviewed-by、待 v3 收尾；可持续观察。

## 参考链接
- Jemmy 的 v3 确认询问：https://lore.kernel.org/all/8105C521-9372-4E1D-8C2B-F44D9F8DD287@gmail.com/
