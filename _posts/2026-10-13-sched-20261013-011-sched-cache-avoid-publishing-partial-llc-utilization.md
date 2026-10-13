---
id: sched-20261013-011
subject: 'sched/cache: Avoid publishing partial LLC utilization'
date: 2026-10-13
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
  review_outcome: Prateek 建议 LBF_ALL_PINNED 便宜检查，Jemmy 反驳其语义不匹配
- version: v2
  msgid: <20261013084338.55100-1-jemmywong512@gmail.com>
  date: 2026-10-13
  summary: LBF_ALL_PINNED || !cpumask_subset 折中，补 Fixes/Suggested-by
  review_outcome: Tim Chen 确认方向、要求补 Fixes（已补）
upstream_commit: null
fixes_commit: f025ef275388
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 待 SCHED 维护者 review/收取
  next_action: 维护者 review v2 后合入
contribution_opportunities:
- kind: testing
  description: 在启用 cache-aware 调度环境验证亲和性重试与 hotplug 两种窗口下的行为
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261010-004
- sched-20261012-007
tags:
- load_balance
title: 'sched/cache: Avoid publishing partial LLC utilization'
layout: article
---

> **subject**：sched/cache: Avoid publishing partial LLC utilization

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-004-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261010-004</a>：Jemmy Wong 修 cache-aware 调度「部分 LLC 利用率」问题——`update_sg_lb_stats()` 对 `sched_group_span(group)` 与 `env->cpus` 两个可能不一致的集合求和利用率，`record_sg_llc_stats()` 把「部分利用率 + 完整容量」一起发布，让 `can_migrate_llc()` 误判忙碌的 preferred LLC 有空余。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-007-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261012-007</a>：Prateek 建议用更便宜的 `LBF_ALL_PINNED` 标志替代 `cpumask_subset()`；Jemmy 反驳该标志语义不匹配、漏掉 hotplug 窗口。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-011-sched-cache-avoid-publishing-partial-llc-utilization.html">sched-20261013-011</a>（今天）：Jemmy 发 **v2**——折中方案 `(env->flags & LBF_ALL_PINNED) || !cpumask_subset(...)`（先便宜标志、再子集检查），并补 `Fixes:` 与 `Suggested-by`；Tim Chen 确认「partial group 问题成立、LBF_ALL_PINNED 先行 + cpumask_subset 兜底」的方向，要求补 Fixes 标签。

## 背景与问题
（承接 20261010-004 → 20261012-007）当负载均衡因 all-pinned 而 redo、或 CPU hotplug 使 `env->cpus` 与 `sched_group_span(group)` 不一致时，若把只覆盖部分 CPU 的利用率当整组利用率发布，`can_migrate_llc()` 会误判忙碌的 preferred LLC 为有富余容量，导致任务过度聚合、迁出受阻、争用与时延加剧（作者标注「Found by inspection」）。

## 技术方案
（承接 20261010-004）v2 采纳 Prateek 与 Tim 的折中（`kernel/sched/fair.c` +8）：
- 在 `record_sg_llc_stats()` 开头加 `if ((env->flags & LBF_ALL_PINNED) || !cpumask_subset(sched_group_span(group), env->cpus)) return;`——亲和性重试用便宜的 `LBF_ALL_PINNED` 标志跳过发布并保留首轮快照、避免重复 cpumask 检查；hotplug 首轮的「组未完整覆盖」仍由 `cpumask_subset()` 兜底。
- 注释说明 redo 会重复首轮已发布的统计、hotplug 仍可能让 `env->cpus` 残缺。
- 补 `Fixes: f025ef275388 ("sched/cache: Record per LLC utilization to guide cache aware scheduling decisions")` 与 `Suggested-by: K Prateek Nayak / Tim Chen`。

## 版本演进与当前进展
v2 今日首发（`<20261013084338.55100-1-jemmywong512@gmail.com>`）。相对 v1：改走 LBF_ALL_PINNED + cpumask_subset 折中、更新注释与提交信息、补 Fixes/Suggested-by 标签。Tim Chen 当日即确认方向。

## Maintainer 意见与讨论焦点
- **Tim Chen**（cache-aware 调度作者）：确认 partial group 问题有效、赞同 Prateek 的「LBF_ALL_PINNED 先行 + cpumask_subset 兜底」、要求补 Fixes 标签；并 CC 该函数的原作者 Chen Yu。
- **K Prateek Nayak**（前日）：提出 LBF_ALL_PINNED 便宜检查，v2 已吸收。
- 无 NAK；方向已获关键评审认可。

## 合入评估
*likelihood=medium*。修复方向获 Tim/Prateek 认可、v2 已按意见落地并补 Fixes 标签，但尚需 Peter/Vincent 等 SCHED 维护者收取。*blocking_issues*：待 SCHED 维护者 review/收取。*next_action*：维护者 review v2 后合入。

## 效果评估
无性能数字；问题为逻辑正确性（作者「Found by inspection」），修复避免误发布部分利用率。作者未提供复现/压测数据。

## 我可以参与的点
- review/testing：可在启用 cache-aware 调度（LLC utilization 记录）的环境下验证 v2 的 `LBF_ALL_PINNED || !cpumask_subset` 判断在亲和性重试与 hotplug 两种窗口下的行为，回帖确认。

## 参考链接
- v2 lore：https://lore.kernel.org/all/20261013084338.55100-1-jemmywong512@gmail.com/
- v1 lore：https://lore.kernel.org/all/20261010113425.34829-1-jemmywong512@gmail.com/
