---
id: sched-20261110-010
date: '2026-11-10'
subject: Improving latency of short slice tasks
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <CAKfTPtA-nrgGQGcBPqNoPk4atOHakyZK9Fk-4AsrHBrnvPXTLQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CAKfTPtA-nrgGQGcBPqNoPk4atOHakyZK9Fk-4AsrHBrnvPXTLQ@mail.gmail.com/
authors:
- Vincent Guittot
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v3
patch_series:
- version: v3
  msgid: <20261106151947.3991524-1-vincent.guittot@linaro.org>
  date: '2026-11-06'
  summary: 20 补丁：正 lag 衰减 + 选 CPU 考虑 slice + fair 类 push 回调
  review_outcome: Peter/Kayra 评审收口：02/06/08 作者逐条回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08 push 机制实现方式（新列表 vs 复用 cfs_tasks）待 Peter 再评
  - 02 是否用 WRITE_ONCE 待作者实测后定
  next_action: 作者据今日收口出 v4
contribution_opportunities:
- kind: review
  description: 就 08 独立 push 列表在数万任务排队场景的开销给出实测或分析
- kind: testing
  description: 验证 06/20 在含 RT 任务负载下是否误选有 RT 任务在跑的 CPU
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 5
related_articles:
- sched-20261106-002
- sched-20261107-004
- sched-20261109-002
tags:
- eevdf
- cfs
- perf
title: Improving latency of short slice tasks
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a>：Vincent Guittot（sched/fair 维护者）的 v3 大系列（20 补丁）改进短 slice 任务调度延迟：正 lag 衰减、选 CPU 考虑 slice、fair 类新增 push 回调、让 feec() 按 cost+slice 选 CPU、修复多任务同时醒来堆叠同一 idle CPU。dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%；cyclictest 99.9 分位略回退。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-004-improving-latency-of-short-slice-tasks.html">sched-20261107-004</a>：Kayra Cizmeci 密集评审 patch 02–06/20，对 03/04/05 给 Reviewed-by，对 02 提 WRITE_ONCE 配对、对 06 提「排除有 RT 任务在跑的 CPU」实质担忧。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-002-improving-latency-of-short-slice-tasks.html">sched-20261109-002</a>：Peter Zijlstra 亲自评审——对 08/20 质疑「为何新增列表与 plist，rq->cfs_tasks 本身就是 MRU 序」，对 02/20 判定「无 WRITE_ONCE 逻辑可行但 KCSAN 告警」，对 06/20 指出 `READ_ONCE` 应为 `rcu_dereference_all()` 且只选最早一个 slice_cpu 的语义问题。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-010-improving-latency-of-short-slice-tasks.html">sched-20261110-010</a>（今天）：**Vincent 逐条收口这些评审**——02 同意至少补注释、并实测 WRITE_ONCE 代价后决定是否采用；06 承认会顺带修 `set_idle_cores`（评审者指出的遗漏）；08 解释为何坚持独立小列表 + 复用 `plist_node pushable_tasks`（`rq->cfs_tasks` 可能很长、plist 只为复用已有结构、目标是保持 push 候选列表很小以控制迁移节奏）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-002-improving-latency-of-short-slice-tasks.html">sched-20261106-002</a> / 20261107-004 / 20261109-002）短 slice 任务在 EEVDF 下因 slice 短、lag 反复累积而排不上队，多任务同时醒来堆叠同一 idle CPU；Vincent 的 v3 20 补丁用「正 lag 衰减 + 选 CPU 考虑 slice + fair 类 push 回调」解决。今日进入评审收口：作者对 Peter/Kayra 的质疑逐条回应，尚未出新版。

## 技术方案

今日为评审回应、无新代码，焦点在三个补丁的设计取舍：

- **02/20 `Reset lag at wakeup when prev CPU has been idle`**：Vincent 同意至少补注释，并称「会跑些测试、若 WRITE_ONCE 无差异就用它」，回应 Peter 的 KCSAN 顾虑。
- **06/20 `Add min slice check when selecting CPU`**：Vincent 确认会顺带修 `set_idle_cores`（评审者指出的遗漏点）。Kayra 复述其关注点集中在 06 与 02，并提醒 sashiko 也提了其它顾虑、建议一并看。
- **08/20 `Add push task mechanism for fair`**：Vincent 解释设计——`rq->cfs_tasks` 可能很长（LB 时甚至要喘口气），而专门的小列表大部分时候只有 1 个任务（wakeup 时除外）；用 plist 只是复用 `struct plist_node pushable_tasks`（RT 里已有），并担心遍历超长 `rq->cfs_tasks` 的开销（社区见过数千任务排队在同一 rq 的 bug 邮件）；目标是保持 push 候选列表很小，所以只检查「prev 能否被 push 到别处」，且 migrate-disabled 任务要等到下次变 current 后才处理，以此给单次回调里 push 的任务数限速。

## 版本演进与当前进展

*current_version: v3（2026-11-06 发出，20 补丁）*。今日仍为评审回应日、无新版本：Vincent 对 02/06/08 的评审给出收口答复，Kayra 的 06 关注得到确认。预期作者据此出 v4。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（作者兼 sched/fair 维护者）**：对 Peter 的 08 结构性异议（复用 rq->cfs_tasks）给出坚持独立小列表的理由（长度、迁移节奏、复用 plist_node）；对 02 的 KCSAN 顾虑以「先补注释、实测后决定 WRITE_ONCE」折中；对 06 承认遗漏并承诺修。
- 分歧仍集中在 08 的 push 实现（新列表 vs 复用 cfs_tasks），作者已给出技术理由，但 Peter 是否接受尚未见回应。

## 合入评估

*likelihood=medium*。作者是本子系统维护者、系列被 Peter 积极评审，且今日多条评审点已收口；但 08 的实现方式分歧（新列表 vs 复用）仍是结构性未决，02 的 KCSAN 处理也未最终定。*blocking_issues*：① 08 push 机制实现方式待 Peter 再评；② 02 是否用 WRITE_ONCE 待作者实测后定。*next_action*：作者据今日收口出 v4（02 注释/实测、06 set_idle_cores、08 维持小列表并附理由）。

## 效果评估

今日无新增性能数据。既有数据（20261106-002）：dragonboard rb5 上 4 短任务同时醒来平均延迟约 1051us→61us，hackbench pipe +15-25%，cyclictest 99.9 分位略回退（正 lag 衰减所致，作者已知）。

## 我可以参与的点

- **review**：就 08「独立小 push 列表 vs 复用 rq->cfs_tasks」在数万任务排队场景下的真实开销给出实测或分析（作者已给出担忧，社区数据可帮助定论）。
- **testing**：在含 RT 任务的混合负载下验证 06/20 min slice 选 CPU 是否误选「有 RT 任务在跑」的 CPU（Kayra 的实质担忧，今日仍未见直接回应的数据）。

## 参考链接

- lore thread（系列 cover）: https://lore.kernel.org/all/20261106151947.3991524-1-vincent.guittot@linaro.org/
- Vincent 对 08 的回应: https://lore.kernel.org/all/CAKfTPtA-nrgGQGcBPqNoPk4atOHakyZK9Fk-4AsrHBrnvPXTLQ@mail.gmail.com/
- Vincent 对 02 的回应: https://lore.kernel.org/all/CAKfTPtAL9T0bGZdhkodC49DtNUFKJgEn9f5wLNBe_rGxzJEN0w@mail.gmail.com/
- Kayra 对 06 的复述: https://lore.kernel.org/all/avIh4MZjVyQuF6Yo@scheduler.schedules/
