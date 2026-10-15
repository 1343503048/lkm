---
id: sched-20261015-023
date: 2026-10-15
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
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
  summary: SCHED_IDLE_SMT_PRIO 静态分支 + 架构钩子，宁可整核空闲不占忙核 SMT 兄弟
  review_outcome: 多轮讨论；Vincent 反对 rebuild topology + 阈值，主张容量/压力导向
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Vincent 不认可 rebuild topology + 阈值路径，要求容量/压力导向
  next_action: Mete 回应 Vincent 方向建议，评估容量修正 + pressure 反馈路线
contribution_opportunities:
- kind: discussion
  description: 参与修正 per-CPU capacity + pressure 反馈取代 idle-SMT 阈值的设计
- kind: review
  description: 评估 cpu_preferred_mask 三档方案与容量修正路线的复杂度与性能影响
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles:
- sched-20261008-001
- sched-20261009-013
- sched-20261012-011
- sched-20261013-010
- sched-20261014-014
tags:
- topology
- cfs
- hyperthreading
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a> / 20261009-013：Mete Durlu（IBM/s390）发 RFC——非对称容量 + SMT 系统上调度器「宁可整核空闲也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + 架构钩子；Andrea/Shrikanth 建议改走扩展 `cpu_preferred_mask` 做 soft preference。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-011-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261012-011</a>：Vincent Guittot 反对「运行期容量可变」假设，指向 Shrikanth 的 preferred-core 工作；Mete 提出三档 `cpu_preferred_mask + soft affinity` 方案。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-010-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261013-010</a>：Mete 用 ASCII 放置图细化三档/soft-affinity 思路；Shrikanth 质疑。
- <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-014-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261014-014</a>：Shrikanth 认为示例成立但现实影响被放大，建议用合理 steal 阈值实测；soft affinity 实现 tricky。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-023-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261015-023</a>（今天）：Vincent 表示「重建 topology 虽安全但昂贵」，主张用调度器收到的压力（steal/hw）判定 CPU 是否变低效，并「修正 per-CPU capacity」而非加阈值来决定 pack/spread。

## 背景与问题
（承接 20261008-001 → 20261014-014）s390 vCPU 有极化（高低 entitlement）概念：无争用时 vCPU 容量近乎对称，steal time 越阈值后低 entitlement vCPU 才降容量；此时「低容量但整核空闲」的核不应再被优先，应先打包到高容量核的 SMT 兄弟。今日聚焦 Vincent 对整体方向的重新表态。

## 技术方案
（承接 20261013-010/20261014-014）今日无新代码，是方向性分歧的进一步展开。Vincent 的两点：
1. 作者方案里「重建 topology（`rebuild_sched_domains()`）」虽安全但昂贵，不认可作为常规路径；
2. 主张用调度器已收到的压力（steal 或 hw pressure）来判定某 CPU 是否变得比其它 CPU 低效；用「正确的 per-CPU capacity」来决定某 idle 低容量核是否优于已忙高容量核的 sibling，而不是加一个「是否 pack/spread 到 idle core」的阈值。

## 版本演进与当前进展
- RFC 多轮讨论后，今日 Vincent 给出方向性纠偏：不要靠 topology 重建 + 阈值，应靠容量修正 + 压力反馈。

## Maintainer 意见与讨论焦点
Vincent Guittot 明确反对「rebuild topology」与「加阈值」两条实现路径，主张回到「修 capacity + 用 pressure 反馈」的正交方向。这与 Mete 此前「三档 preferred mask + soft affinity」思路存在实质分歧，尚未收敛。

## 合入评估
*likelihood=medium*。问题真实、多方关注，但实现方向在作者与维护者之间仍有分歧（rebuild topology vs 容量修正），需进一步对齐。*blocking_issues*：Vincent 不认可 rebuild topology + 阈值的实现路径，要求容量/压力导向。*next_action*：Mete 回应 Vincent 的方向建议，评估「修正 per-CPU capacity + pressure 反馈」是否可行，或给出不重建 topology 的替代实现。

## 效果评估
无量化数据；讨论停留在设计层面，未见基准。

## 我可以参与的点
- *discussion*：参与「用修正后的 per-CPU capacity + pressure 反馈取代 idle-SMT 阈值」的方案设计，尤其 s390 steal 反馈与通用 hw pressure 如何接入选核。
- *review*：评估 `cpu_preferred_mask` 三档方案与「容量修正」路线各自的复杂度和性能影响。

## 参考链接
- Vincent 的方向性意见：https://lore.kernel.org/all/CAKfTPtC70sx58uiaMEXv=vOk+o-Q_1PcHewiVjGCWMd_kvn=tA@mail.gmail.com/
- 原始 RFC：https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
