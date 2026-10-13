---
id: sched-20261013-010
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
date: 2026-10-13
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
authors:
- Mete Durlu
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
  date: 2026-10-08
  summary: SCHED_IDLE_SMT_PRIO 静态分支 + arch_needs_idle_smt_prio() 钩子
  review_outcome: 多轮评审，soft affinity/三档方案演进中，前提仍被质疑
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Shrikanth 对「低容量核该被规避」的前提质疑未闭环
  - 与 Vincent「容量不应运行期变」立场待调和
  next_action: 作者回应何时规避低容量核、与评审就 soft affinity 表达达成一致
contribution_opportunities:
- kind: discussion
  description: 帮助形式化「低容量核规避」触发条件，或评估 soft-affinity-as-cpumask 成本
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 4
related_articles:
- sched-20261008-001
- sched-20261009-013
- sched-20261012-011
tags:
- cfs
- topology
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

> **subject**：sched: Introduce idle SMT priority for asymmetric capacity systems

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a> / 20261009-013：Mete Durlu（IBM/s390）发 RFC——非对称容量 + SMT 系统上调度器「宁可整核空闲也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + `arch_needs_idle_smt_prio()` 钩子；Andrea/Shrikanth 建议改走扩展 `cpu_preferred_mask` 做 soft preference。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-011-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261012-011</a>：Vincent Guittot 反对「运行期容量可变」假设，指向 Shrikanth 的 preferred-core 工作；Mete 提出三档 `cpu_preferred_mask + soft affinity` 方案。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-010-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261013-010</a>（今天）：Mete 用 ASCII 放置图细化了三档/soft-affinity 思路（steal time 在 low/high 阈值之间时先填满高容量核的 SMT 兄弟、再外溢到低容量核），并澄清 idle 负载均衡与「soft affinity 作为独立 cpumask」的取舍；Shrikanth 则质疑前提——若无系统压力、任务 util 又 fits 低容量核，为何不直接用低容量核。

## 背景与问题
（承接 20261008-001 → 20261012-011）s390 上 vCPU 有极化（高低 entitlement）概念：无争用时所有 vCPU 容量近乎对称，steal time 越过阈值后低 entitlement vCPU 才降容量；此时「低容量但整核空闲」的核不应再被优先，应先把负载打包到高容量核的 SMT 兄弟。今天的讨论把问题进一步聚焦到「soft affinity 到底要表达什么、以及低容量核在何种条件下才该被规避」。

## 技术方案
（承接 20261008-001）原 RFC 为静态分支 + 架构钩子；12 日 Mete 已提出三档方案（steal time==0 → 无 soft affinity 维持整核空闲优先；0 < steal ≤ 阈值 → soft affinity 先填满 entitled 核 SMT 兄弟再外溢；> 阈值 → preferred mask 收缩）。今日 Mete 补充：
- 用 ASCII 放置图说明当前行为（优先整核空闲、即使低容量）与提案行为（优先高容量核的 SMT 兄弟、再整核空闲）的差异，并说明「先填高容量核」能降低 guest 足迹、减少对邻分区噪声。
- 认为 soft affinity 可表达为「另一个 cpumask」：先遍历该 mask 做决策，其资源耗尽后再落到 `cpu_preferred_mask`。
- 对 Shrikanth 关于 idle 负载均衡的追问表示「本意是任务放置决策，未特别考虑 idle load balancing，s390 上即便发生在非 preferred CPU 也无大碍」。
- 提议沿用 steal governor 的 `low_threshold` 思路做「初始阈值」，但需再想是否用更高默认值。

Shrikanth 的核心质疑：若没有系统压力去用低容量核、任务 util 又 fits 其容量，为何不用它们（它们今天也不会被 util 超限的任务选中）——即问题是否真实存在，取决于「低容量核该被规避」这一前提是否成立。

## 版本演进与当前进展
仍为 RFC v1，无新版本补丁；今日为方案细节与前提的持续讨论（Mete 细化 soft affinity/三档，Shrikanth 质疑前提）。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（mainline 维护者，前日）：反对运行期容量可变，主张走 Shrikanth 的 preferred-core 机制。
- **Shrikanth Hegde**（今日）：质疑「为何不直接用 fits 的低容量核」，要求作者把「低容量核该被规避」的触发条件讲清楚。
- **Mete Durlu**（作者）：坚持「无争用/低于阈值时整核空闲优先尚可、争用期应先填高容量核 SMT 兄弟」，但承认需进一步想阈值设计。
- 分歧未收敛：作者尚未把「何时规避低容量核」与 steal governor 阈值的关系形式化。

## 合入评估
*likelihood=medium*。方案在持续演进、有多方评审，但核心前提（低容量核规避的触发条件）仍被质疑，且实现路线（静态分支 vs preferred-core 扩展）未定。*blocking_issues*：Shrikanth 的前提质疑未闭环；与 Vincent「容量不应运行期变」的立场待调和。*next_action*：作者回应「何时该规避低容量核」、与 Shrikanth/Andrea 就 soft affinity 的 mask 表达达成一致。

## 效果评估
暂无 benchmark 数字；讨论为放置行为设计，作者用示意放置图而非实测数据论证。

## 我可以参与的点
- discussion：帮助作者把「低容量核应被规避」的触发条件形式化（与 steal governor 阈值、极化状态的关系），或评估 soft-affinity-as-cpumask 的表达成本。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- 今日 Mete 细述：https://lore.kernel.org/all/ce85388c-3ea0-4363-8c89-fe2bf71b284a@linux.ibm.com/
