---
id: sched-20261029-005
date: 2026-10-29
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
subsystem: sched
type: discussion
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
  summary: RFC 0/2：SCHED_IDLE_SMT_PRIO 静态分支 + 架构钩子，让调度器优先打包到高容量核的 SMT 兄弟
  review_outcome: Vincent 反对运行期容量可变假设；Shrikanth 拆解为容量偏好 + 压力避让两线
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 缺「选 idle 垂直高 SMT CPU 是否总更优」的实测结论
  - 缺合理 steal 阈值下的 benchmark 支撑
  - 作者未回应 Vincent/Shrikanth 的方向性拆解
  next_action: 作者按容量偏好/压力避让两线重组方案并补实测数据
contribution_opportunities:
- kind: testing
  description: 在高/低 entitlement 环境用不同 steal 阈值实测两种放置策略的性能，给出子问题 1 结论
- kind: discussion
  description: 推动作者对「复用 ASYM_PACKING/select_idle_capacity + steal governor」方向表态
generated_at: '2026-10-30T09:30:00'
source_email_count: 1
related_articles:
- sched-20261008-001
- sched-20261009-013
- sched-20261012-011
- sched-20261013-010
- sched-20261014-014
- sched-20261015-023
tags:
- topology
- load_balance
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-001-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261008-001</a> / 20261009-013：Mete Durlu（IBM/s390）发 RFC——非对称容量 + SMT 系统上调度器「宁可整核空闲也不占忙碌高容量核的空闲 SMT 兄弟线程」，引入 `SCHED_IDLE_SMT_PRIO` 静态分支 + 架构钩子；Andrea/Shrikanth 建议改走扩展 `cpu_preferred_mask` 做 soft preference。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-011-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261012-011</a>：Vincent Guittot 反对「运行期容量可变」假设，指向 Shrikanth 的 preferred-core 工作；Mete 提出三档 `cpu_preferred_mask + soft affinity` 方案。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-010-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261013-010</a> / 20261014-014：Mete 用 ASCII 放置图细化；Shrikanth 质疑示例影响被放大，建议用合理 steal 阈值实测。
- <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-023-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261015-023</a>：Vincent 主张用调度器已收到的压力（steal/hw）判定 CPU 是否变低效，并「修正 per-CPU capacity」而非加 pack/spread 阈值。
- <a class="article-ref" href="/lkm/2026/10/29/sched-20261029-005-sched-introduce-idle-smt-priority-for-asymmetric-capacity-sy.html">sched-20261029-005</a>（今天）：Shrikanth 给 Mete 一个「一分为二」的框架性建议——①「垂直高 SMT idle CPU 是否总优于垂直低 SMT idle core」若成立，该走 ASYM_PACKING / `select_idle_capacity`；②若只是「高 steal 下避让垂直低核」，则走 steal governor，必要时加架构钩子（仅在 HW 压力下，而非始终）。

## 背景与问题
（承接 20261008-001 → 20261015-023）s390 vCPU 有极化（高低 entitlement）概念：无争用时 vCPU 容量近乎对称，steal time 越过阈值后低 entitlement vCPU 才降容量。此时「低容量但整核空闲」的核不应再被优先，应先打包到高容量核的 SMT 兄弟。核心难题是：这个「先选谁」的决策，是该做成静态优先级钩子，还是复用既有的容量/压力信号。今日 Shrikanth 把问题重述为两个正交子问题，帮助厘清方案归属。

## 技术方案
今日无新代码，是方向性拆解。Shrikanth Hegde 的建议：

1. **子问题 1**：如果结论是「选 idle 垂直高 SMT CPU 总比 idle 垂直低 SMT core 更优」（与系统压力/steal 无关），那需要的是类似 **ASYM_PACKING** 或 **`select_idle_capacity`** 的机制——把「垂直高 vs 垂直低」编码成容量/优先级，而非静态 SMT 优先级钩子。
2. **子问题 2**：如果只是想「高 steal 时间下避让垂直低核」，那 **steal governor** 才是正确方向；现有逻辑达不到时可加架构钩子，但只在 **HW 压力下** 生效，不是始终生效。

这承接 Vincent 的「用压力信号 + 修正 per-CPU capacity」判断，实质是把作者原 RFC 的单一静态机制拆成「容量偏好」与「压力避让」两条独立路径。

## 版本演进与当前进展
*current_version: v1 (RFC)*（2026-10-08 首发，线程根 `<20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>`）。至今无 v2，长期处于设计讨论阶段；今天 Shrikanth 给的是方案重述（一分为二），未改变补丁状态。

## Maintainer 意见与讨论焦点
- **Vincent Guittot（维护者，20261012/20261015）**：反对「运行期容量可变」的假设；「重建 topology 虽安全但昂贵」不认可作为常规路径；主张用调度器已收到的压力（steal/hw）判定 CPU 是否变低效，用正确的 per-CPU capacity 决定 pack/spread，而非加阈值。
- **Shrikanth Hegde（今天）**：把问题拆为「容量偏好（ASYM_PACKING/select_idle_capacity）」与「高 steal 压力避让（steal governor + 架构钩子）」，指出后者只在 HW 压力下应生效。
- 未解决焦点：作者尚未回复是否接受「一分为二」，以及两个子问题的实测数据（steal 阈值下是否真优于现状）仍缺。

## 合入评估
*likelihood=low*。方向仍在设计讨论阶段，Vincent 与 Shrikanth 都倾向用既有容量/压力信号而非新静态钩子，与作者原 RFC 的形态有出入，需作者改弦。*blocking_issues*：缺「选 idle 垂直高 SMT 是否总更优」的实测结论；缺合理 steal 阈值下的 benchmark；作者未回应方向性拆解。*next_action*：作者按「容量偏好 / 压力避让」两条线重新组织方案并补实测数据。

## 效果评估
无性能数据。Shrikanth 此前认为示例结论成立但现实影响被放大，建议用合理 steal 阈值实测；Mete 的 ASCII 放置图只是定性示意。本线程目前没有任何 benchmark 数字支撑「打包到高容量核 SMT 兄弟」的收益，均属主观判断。

## 我可以参与的点
- **testing**：在具高/低 entitlement 的 s390 环境（或 QEMU 线程模型）下，用不同 steal 阈值实测「整核空闲 vs 占高容量核 SMT 兄弟」两种放置的吞吐/延迟，为子问题 1 提供结论。
- **discussion**：作者需要对 Vincent/Shrikanth 的「复用 ASYM_PACKING/select_idle_capacity + steal governor」方向表态，可在列表上继续推动收敛。

## 参考链接
- lore thread（RFC v1 cover）: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- Shrikanth 今日的拆解建议: https://lore.kernel.org/all/261148c1-48ba-4ede-bad6-24c18ed9d545@linux.ibm.com/
