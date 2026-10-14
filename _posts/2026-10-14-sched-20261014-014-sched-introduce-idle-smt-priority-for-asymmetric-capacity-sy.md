---
id: sched-20261014-014
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
date: 2026-10-14
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
  review_outcome: 多轮评审，待实测支撑与 soft affinity 成本设计
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 待 Mete 用合理阈值实测「低容量核该被规避」的触发条件
  - soft affinity 实现成本未定
  - 与 Vincent「容量不应运行期变」立场待调和
  next_action: Mete 提供实测数据并回应 soft affinity 常见路径开销
contribution_opportunities:
- kind: discussion
  description: 帮助形式化低容量核规避触发条件，或评估 soft-affinity-as-cpumask 常见路径开销
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261008-001
- sched-20261009-013
- sched-20261012-011
- sched-20261013-010
tags:
- cfs
- topology
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

> **subject**：sched: Introduce idle SMT priority for asymmetric capacity systems

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a> / 20261009-013：Mete Durlu（IBM/s390）发 RFC——非对称容量 + SMT 系统上调度器「宁可整核空闲也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + 架构钩子；Andrea/Shrikanth 建议改走扩展 `cpu_preferred_mask` 做 soft preference。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-011-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261012-011</a>：Vincent Guittot 反对「运行期容量可变」假设，指向 Shrikanth 的 preferred-core 工作；Mete 提出三档 `cpu_preferred_mask + soft affinity` 方案。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-010-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261013-010</a>：Mete 用 ASCII 放置图细化三档/soft-affinity 思路；Shrikanth 质疑前提——若无压力、任务 util 又 fits 低容量核，为何不直接用低容量核。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-014-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261014-014</a>（今天）：Shrikanth 回应 Mete 的示例——承认「例子说得通」，但指出配好 steal governor 后争用期 preferred mask 里的低容量核本应很少，**建议用合理阈值实测验证现实效果**；并提醒 soft affinity 实现有成本、需保证常见路径开销最小。

## 背景与问题
（承接 20261008-001 → 20261013-010）s390 上 vCPU 有极化（高低 entitlement）概念：无争用时所有 vCPU 容量近乎对称，steal time 越过阈值后低 entitlement vCPU 才降容量；此时「低容量但整核空闲」的核不应再被优先，应先把负载打包到高容量核的 SMT 兄弟。今日聚焦 Shrikanth 对 Mete 示例的回应。

## 技术方案
（承接 20261013-010）今日无新代码，是前提与实现成本的持续掰扯：

- Shrikanth 认为 Mete 的示例成立，但若 steal governor 阈值配得合理，物理 CPU 争用期 preferred mask 内低容量核数目会非常少，「先在低容量核外溢」的问题现实里可能远不如示例严重。
- 建议 Mete 用合理阈值做实测（默认阈值未必适合所有配置）；也可把 low 阈值压到极低，看 preferred mask 是否就等于 entitled 核数（即 mask 里几乎没有低容量核）。
- 承认 steal governor 是反应式机制、可能有振荡，偶尔放几个低容量核进来。
- **soft affinity 表达「另一个 cpumask」的实现较 tricky**，需确保常见路径（无 affinity/无争用）开销最小。

## 版本演进与当前进展
仍为 RFC v1，无新版本补丁；今日为方案前提与现实成本的双向讨论（Shrikanth 回应 Mete 示例）。

## Maintainer 意见与讨论焦点
- **Vincent Guittot**（mainline 维护者，前日）：反对运行期容量可变，主张走 Shrikanth 的 preferred-core 机制。
- **Shrikanth Hegde**（今日）：认可示例但要求「用合理阈值实测」；提醒 soft affinity 实现成本与常见路径开销。
- **Mete Durlu**（作者）：坚持争用期应先填高容量核 SMT 兄弟，尚未对阈值设计形式化。
- 分歧未收敛：作者仍需用实测证明「低容量核该被规避」的真实触发条件，并落实 soft affinity 的低开销实现。

## 合入评估
*likelihood=medium*。方案持续演进、多方评审，但核心前提（低容量核规避的触发条件）仍待实测支撑，soft affinity 实现成本与「运行期容量可变」立场（Vincent）未调和。*blocking_issues*：待 Mete 用合理阈值实测；soft affinity 实现成本未定；与 Vincent 立场待调和。*next_action*：Mete 提供实际阈值下的观测数据，并回应 soft affinity 的常见路径开销设计。

## 效果评估
暂无 benchmark 数字；Shrikanth 明确指出「需要用合理阈值看现实效果」，作者此前仅用示意放置图论证。

## 我可以参与的点
- discussion：帮助作者把「低容量核应被规避」的触发条件形式化（与 steal governor 阈值、极化状态的关系），或评估 soft-affinity-as-cpumask 在常见路径（无争用）下的实现开销。

## 参考链接
- 系列 cover lore：https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- 今日 Shrikanth 回应：https://lore.kernel.org/all/e6807d57-35af-4b4f-8b81-cabe0dfe99bd@linux.ibm.com/
