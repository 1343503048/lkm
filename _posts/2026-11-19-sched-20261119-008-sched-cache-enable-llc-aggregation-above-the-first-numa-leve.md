---
id: sched-20261119-008
date: '2026-11-19'
subject: 'sched/cache: Enable LLC aggregation above the first NUMA level'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261112065445.592968-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20261112065445.592968-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261112065445.592968-1-wujianyong@hygon.cn>
  date: '2026-11-12'
  summary: 开启第一层 NUMA 之上的 LLC 聚合；补 schbench/hackbench
  review_outcome: Chen Yu 追加 src_cpu 选取建议
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - llc_balance src_cpu 选取待回应
  - 待调度维护者评审
  next_action: 作者回应 Chen Yu 的 src_cpu 建议，或出 v3 修正
contribution_opportunities:
- kind: review
  description: 核对 Chen Yu 的 src_cpu diff 是否等价/更优
- kind: testing
  description: SNC/NPS/多 sub-NUMA 平台复测跨 node 聚合行为
generated_at: '2026-11-20T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261105-008
- sched-20261112-006
tags:
- load_balance
- topology
title: 'sched/cache: Enable LLC aggregation above the first NUMA level'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-008-sched-cache-fix-group-llc-balance-being-unreachable-above-th.html">sched-20261105-008</a>：Jianyong Wu（Hygon）的 v1 修复 cache-aware 调度里 `group_llc_balance` 在第一层 NUMA 之上不可达的缺陷；Tim Chen 给 busiest_llc_balance 重构、Chen Yu 质疑「fix vs 增强」定位并要求补 benchmark。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-006-sched-cache-enable-llc-aggregation-above-the-first-numa-leve.html">sched-20261112-006</a>：**v2 发出**——采纳 Tim Chen 重构、补 NUMA balancing 开/关的 schbench/hackbench 数据、标题从「Fix」改「Enable」并 drop `Fixes:`。schbench p99 唤醒延迟 3/4 线程单 LLC 聚合率 53-80% → 97-100%，延迟改善 15.5%-26.7%。
- <a class="article-ref" href="/lkm/2026/11/19/sched-20261119-008-sched-cache-enable-llc-aggregation-above-the-first-numa-leve.html">sched-20261119-008</a>（今天）：**Chen Yu 对 v2 追加一个技术疑问**——LLC 聚合开放到 NUMA level 2 之后，`llc_balance()` 里用 `cpumask_first(sched_group_span(dst_group))` 取的是「busiest NUMA node 的第一个 CPU」，在 sub-NUMA（如 N2.1/N2.2）场景下可能取错 src_cpu，建议改用「busiest NUMA node 里最忙的 CPU」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-008-sched-cache-fix-group-llc-balance-being-unreachable-above-th.html">sched-20261105-008</a> … 20261112-006）cache-aware 调度此前只允许在第一层 NUMA 内的 LLC 之间聚合任务；v2 把聚合开放到第一层 NUMA 之上。Chen Yu 今天指出由此带来的一个选择偏差：在「每 socket 多 NUMA node、每 node 又有 sub-NUMA」的多层拓扑上，聚合允许跨 node 后，`llc_balance()` 评估 dst LLC 与 src group 首个 CPU 所在 LLC 的利用率时，`cpumask_first(sched_group_span(N2))` 恒定返回 N2.1 的第一个 CPU，而真正的 busiest 可能在 N2.2。

## 技术方案

今日为评审讨论、无新代码：Chen Yu 建议把 `llc_balance()` 里「取 src group 第一个 CPU」改为「取 busiest NUMA node 里最忙的 CPU」，并附了一个 `record_sg_llc_stats()` 附近的 diff 示意。这是对 v2 现有实现的收尾性修正，方向是「src_cpu 应与 busiest 对齐」，避免跨 node 聚合时利用率评估偏差。

## 版本演进与当前进展

*current_version: v2（2026-11-12，`<20261112065445.592968-1-wujianyong@hygon.cn>`）*。今日无新版本；Chen Yu 追加一条针对「跨 NUMA 层后 src_cpu 选取」的修订建议。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel，cache-aware 领域活跃评审）**：对 v2 先前的定位/benchmark 要求已落实，今日给出实现级追问——sub-NUMA 拓扑下 `llc_balance()` 的 src_cpu 应取 busiest 而非首个 CPU，并给出 diff 示意。
- 调度维护者（Peter/Ingo）当日未直接表态。
- 无 NAK；v2 前一轮评审已闭合，今日新增一个实现细节待作者吸收。

## 合入评估

*likelihood=medium*。v2 已有完整 benchmark 与 Intel 侧背书，但 Chen Yu 新提出的 src_cpu 选取问题需作者确认/修正后才算收敛。*blocking_issues*：`llc_balance()` src_cpu 选取待回应；待调度维护者评审。*next_action*：作者回应 Chen Yu 的 src_cpu 建议（或出 v3 修正）。

## 效果评估

本轮无新增数据；沿用 v2 的 schbench p99 与单 LLC 聚合率数据（承接 20261112-006）。Chen Yu 的疑问属正确性风险，暂无新回归数据。

## 我可以参与的点

- **review**：核对 Chen Yu 的 src_cpu diff 是否严格等价/更优，尤其多 sub-NUMA、非对称 busy 情况下的利用率评估。
- **testing**：在 Intel SNC / AMD NPS / 多 sub-NUMA 平台复测 v2+ 修正后的跨 node 聚合行为。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261112065445.592968-1-wujianyong@hygon.cn/
- Chen Yu 评审: https://lore.kernel.org/all/av7XHYkg+XLO+Xm4@chenyu-dev/
