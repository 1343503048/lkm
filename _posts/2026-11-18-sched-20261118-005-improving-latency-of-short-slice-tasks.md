---
id: sched-20261118-005
date: '2026-11-18'
subject: Improving latency of short slice tasks
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
  date: '2026-11-06'
  summary: 20 补丁：正 lag 衰减、slice 选 CPU、fair push 回调、feec 用 cost、修 idle 堆叠
  review_outcome: Peter/Kayra 密集评审，01/20 衰减假设今日辩论
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08/20 push 机制实现方式未定
  - 01/20 衰减假设待实测佐证
  next_action: 作者结合 Kayra 实测与 Peter 对 08/20 的意见出 v4
contribution_opportunities:
- kind: testing
  description: 实测 01/20 两种衰减假设的延迟差异
- kind: review
  description: 对 08/20 push 机制复用 rq->cfs_tasks 还是新列表给出判断
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261109-002
tags:
- eevdf
- cfs
- load_balance
title: Improving latency of short slice tasks
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>：Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）改进短 slice 任务调度延迟：正 lag 衰减、选 CPU 考虑 slice、fair 类新增 push 回调、feec() 按 cost+slice 选 CPU、修多任务同时醒来堆叠同一 idle CPU。dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%；cyclictest 99.9 分位略回退。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-004-improving-latency-of-short-slice-tasks.html">sched-20261107-004</a> / 20261109-002：Kayra 密集评审 02-06/20，Peter 评审 02/06/08（质疑 push 机制为何新增列表、建议复用 rq->cfs_tasks）。
- <a class="article-ref" href="/lkm/2026/11/18/sched-20261118-005-improving-latency-of-short-slice-tasks.html">sched-20261118-005</a>（今天）：**Kayra 与 Vincent 就 01/20「正 lag 衰减」的 `decay_entity_lag()` 假设展开学术式辩论**——Kayra 质疑「睡眠任务按 sleep_time 的 1/3 计运行时间」这一假设，Vincent 用 place_entity 的平均 vruntime 数学推导辩护；Kayra 承认两假设差别不大，表示会实测两者差异。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a> / 20261109-002）EEVDF 下「永恒正 lag」会让长时间睡眠、攒了大量正 lag 的任务在醒来时凭陈旧 lag 抢占短任务。patch 01/20 `Decay positive lag of sleeping entities` 用 `decay_entity_lag()` 在 wakeup 入队时衰减正 lag。今日辩论焦点是：衰减时如何估算「该任务睡眠期间本应运行了多久」——这直接决定衰减系数。

## 技术方案

今日无新代码，聚焦 01/20 的衰减假设：

- **Vincent 的现行实现**：假设睡眠任务「本应运行 sleep_time 的 1/3」（用任务 weight 与 cfs 负载之比折算）。他在回复里给出推导——`place_entity` 后平均 vruntime `avg' = (3*avg - 2)/3 = avg - 2/3`，TA 的 lag 为 4/3；并强调「睡眠时间 > slice 时任务仍可能保持正 lag，取决于同时运行的任务数与 weight」。
- **Kayra 的质疑**：`deadline - vruntime` 本可给出 `slice - work_time`，而 sleep_time 已知；「睡满整个 sleep_time」是另一极端假设，若 `sleep_time + working_time < slice` 且任务未被抢占，它本可跑满整个 sleep_time；1/3 与「跑满」都是假设。Kayra 承认两假设差别不大，表示会实测两者差异（同时质疑「是否值得为它加一个 case」）。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，20 补丁）*。今日为评审/讨论日，无新版本：Kayra 与 Vincent 就 01/20 的衰减假设反复交换意见（4 封），未改代码。Kayra 表示会「play around with the whole series」并实测 1/3 vs 跑满 sleep_time 的差异。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（作者，sched/fair 维护者）**：用数学推导辩护 1/3 假设（公平性权衡：长睡任务保留全部正 lag 不公平，全清也不公平），并解释「Peter 曾建议用 weight/cfs 负载比而非乐观假设」。
- **Kayra Cizmeci（reviewer）**：质疑 1/3 假设的合理性（睡眠任务实际运行时间不可知），倾向「跑满 sleep_time」为 less-bad 假设，但承认差别不大、愿意实测。
- 无 NAK；这是设计级学术讨论，双方对最终取值持开放态度，等待 Kayra 的实测数据。

## 合入评估

*likelihood=medium*。系列被维护者与资深 reviewer 持续评审，但 20 补丁规模大、触及热路径；01/20 的衰减假设虽有辩论但双方承认差别不大，不构成阻塞。主要阻塞仍是 08/20 push 机制的实现方式（承接 20261109-002）。*blocking_issues*：① 08/20 push 机制实现方式未定；② 01/20 衰减假设待 Kayra 实测佐证。*next_action*：作者根据 Kayra 实测与 Peter 对 08/20 的意见出 v4。

## 效果评估

今日无新增数据。既有（20261106-002）：4 短任务同时醒来平均延迟约 1051us→61us、hackbench pipe +15-25%、cyclictest 99.9 分位略回退（正 lag 衰减所致）。Kayra 预告将实测 01/20 两种衰减假设的差异。

## 我可以参与的点

- **testing**：复现 Kayra 提出的「1/3 vs 跑满 sleep_time」两种衰减假设的调度延迟差异（尤其多短任务 + 长睡任务混合负载），为 01/20 的系数选择提供数据。
- **review**：就 08/20 push 机制「复用 rq->cfs_tasks 还是新列表」（Peter 提出、未定论）给出实现/复杂度判断。

## 参考链接

- lore thread（v3 cover）: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- Kayra 对 01/20 的质疑: https://lore.kernel.org/all/av2KuYNx1A-rCz0R@scheduler.schedules/
- Vincent 的数学推导: https://lore.kernel.org/all/CAKfTPtBZ=Dc_X48EQ0yXMym0JrS=pWvbviyVyFri0tv5VdR3Eg@mail.gmail.com/
