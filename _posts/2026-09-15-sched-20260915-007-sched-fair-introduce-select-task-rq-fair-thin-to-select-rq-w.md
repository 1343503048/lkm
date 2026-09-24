---
id: sched-20260915-007
date: '2026-09-15'
subject: 'sched/fair: Introduce select_task_rq_fair_thin() to select rq when LB_PROMOTE'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260912040804.3391229-1-jackzxcui1989@163.com>
lore_url: https://lore.kernel.org/all/CAKfTPtCa-Aycx7Lt9Nj7JDs8bdq0oZCt-k_cZR3WiG7YJhBTng@mail.gmail.com/
authors:
- Xin Zhao
maintainers_involved:
- Vincent Guittot
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - sched_feature 动态开关被维护者反对
  - real-time 立意需改为 interactive 叙事
  - 未与 EEVDF slice 做排序语义对比
  next_action: 作者回应三条意见，改 sched_feature 接口并补 EEVDF 对比论证
contribution_opportunities:
- kind: discussion
  description: 分析 LB_PROMOTE 与 EEVDF slice 的排序语义差异，帮作者回应为何需要 LB_PROMOTE
- kind: review
  description: 核对 10 补丁系列中 sched_feature 的使用点并提出替代接口建议
generated_at: '2026-09-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20260912-011
- sched-20260911-009
- sched-20260910-001
tags:
- load_balance
- cfs
title: 'sched/fair: Introduce select_task_rq_fair_thin() to select rq when LB_PROMOTE'
layout: article
---

## TL;DR
本文为增量更新（系列全貌见 related_articles）。Vincent Guittot 09-15 对 Xin Zhao 的 LB_PROMOTE RFC（patch 05/10 引入 `select_task_rq_fair_thin()`）给出三条反馈：把「real-time」字样用于 fair 调度是误导（fair 不是实时调度器，只能保证 best effort）；建议看 EEVDF slice 如何（有限度地）给任务排序；明确不赞成用 `sched_feature` 来使能 LB_PROMOTE——`sched_feature` 是用来评估特性影响的，不是动态开关。

## 背景与问题
承 sched-20260912-011：Xin Zhao 的 10 补丁 RFC 系列用 LB_PROMOTE 机制改善 CFS 任务的调度时延/「实时性」体感，patch 05/10 引入 `select_task_rq_fair_thin()` 在 LB_PROMOTE 时选 rq。Vincent 此前已质疑「有实时需求为何不用 RT 调度器」并否定 LB_PROMOTE 前提；本日就术语、调度语义与实现接口持续给出意见。

## 技术方案
本日无新代码。Vincent 的三点意见均针对设计与方向：
1. 术语：「real-time」用于 fair 调度有误导性，社区惯用「interactive」来描述此类 best-effort 时延优化；
2. 排序语义：如关注 timeliness，应先看 EEVDF slice 作为（有限度的）任务排序手段；
3. 接口：反对用 `sched_feature` 动态使能 LB_PROMOTE——`sched_feature` 是「评估某特性影响时临时开」的测试手段，不应做 enable/disable 开关。

## 版本演进与当前进展
本日为系列 05/10 线程的维护者反馈，无新版本发出。作者当日尚未在本线程回应这三条意见。

## Maintainer 意见与讨论焦点
- **Vincent Guittot (Linaro, sched 维护者)**：术语纠正（real-time → interactive）、建议参考 EEVDF slice、反对 sched_feature 动态开关。
- 争议点：作者用「real-time performance」作为系列立意（见 series 标题），与维护者「fair 不是实时」的立场直接冲突；`sched_feature` 的使用方式被明确否定，作者需换实现接口。

## 合入评估
*likelihood=medium*。方向未获维护者认可（术语与立意、sched_feature 接口两处实质分歧），作者需换接口并重定位立意，但维护者仍在给建设性意见、未 NAK。*blocking_issues*：sched_feature 动态开关被反对；「real-time」立意需改为 interactive 叙事；EEVDF slice 对比未做。*next_action*：作者回应三条意见，改 sched_feature 为实现层默认开关或独立 sysctl，并补与 EEVDF 的对比论证。

## 效果评估
无效果数据。本日为设计层面的维护者反馈，不涉及 benchmark。

## 我可以参与的点
- kind=discussion：就 LB_PROMOTE 与 EEVDF slice 的排序语义差异做分析回帖，帮作者回应「为什么需要 LB_PROMOTE 而非 EEVDF」。
- kind=review：核对系列中 `sched_feature` 的使用点（10 补丁系列多处）并提出替代接口建议。

## 参考链接
- Vincent Guittot 回帖：https://lore.kernel.org/all/CAKfTPtCa-Aycx7Lt9Nj7JDs8bdq0oZCt-k_cZR3WiG7YJhBTng@mail.gmail.com/
- 05/10 补丁：https://lore.kernel.org/all/20260912040804.3391229-1-jackzxcui1989@163.com/
