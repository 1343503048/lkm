---
id: sched-20261115-007
date: '2026-11-15'
subject: 'sched/docs: Rewrite sched-eevdf.rst'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261114183618.56111-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20261114183618.56111-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261114183618.56111-1-kayracizmeci@gmail.com>
  date: '2026-11-15'
  summary: 重写 sched-eevdf.rst，补充核心概念公式与示例
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待维护者核对文档公式与概念表述的准确性
contribution_opportunities:
- kind: review
  description: 逐条核对 weight/vruntime/V/lag 公式与 delayed dequeue 描述是否与内核实现一致
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- eevdf
title: 'sched/docs: Rewrite sched-eevdf.rst'
layout: article
---

## TL;DR

Kayra Cizmeci 重写 EEVDF 文档 sched-eevdf.rst（+155/-39），补充 V、vruntime、deadline、eligibility、lag、delayed dequeue 等核心概念的公式与数值示例，并修复一处指向随机回复而非 cover letter 的引用链接。文档类改动，当日无 review。

## 背景与问题

现版 sched-eevdf.rst 对大多数 EEVDF 核心概念语焉不详（intro commit 也承认这一点），且第二个参考链接指向一个随机回复页而非 Peter Zijlstra 的 cover letter。作者整体重写，弥补概念覆盖与引用准确性两处不足。

## 技术方案

重写 Documentation/scheduler/sched-eevdf.rst：从「Core Basics」讲起，给出 weight/vruntime/V 的公式（`(delta * NICE_0_LOAD) / weight`、`Sum(weight*vruntime)/Sum(weight)`）；定义 eligibility（vruntime ≤ V）、deadline（`vruntime + (slice*NICE_0_LOAD)/weight`，slice 默认 sysctl_sched_base_slice 0.70ms）；讲 lag（`V - vruntime`）与睡眠任务的 lag placement 修正公式（`(Sum(weight)+weight)*lag/Sum(weight)`）；并用 delayed dequeue 的负 lag 例子说明两种结束方式。全篇配数值示例表，References 修正为正确链接。

## 版本演进与当前进展

*current_version: v1（2026-11-15，`<20261114183618.56111-1-kayracizmeci@gmail.com>`）*。当日发出，暂无 review。

## Maintainer 意见与讨论焦点

当日无维护者回帖。文档的技术准确性（公式、示例、delayed dequeue 行为描述）需维护者或 EEVDF 相关工作作者核对。

## 合入评估

*likelihood=unknown*。文档改进方向明确，但公式/概念表述的正确性待 review。*blocking_issues*：无实质分歧，等待 review 确认技术准确性。*next_action*：等待调度维护者（尤其 Peter 及 EEVDF 相关工作作者）核对公式与示例。

## 效果评估

无可量化数据；效果体现在文档可读性与概念覆盖度。

## 我可以参与的点

- **review**：逐条核对 Weight/vruntime/V/deadline/lag 公式与 delayed dequeue 描述是否符合内核实际实现（尤其 lag placement 的 scaling 公式、sysctl_sched_base_slice 默认值、以及 delayed dequeue 结束时是否真的「从 runqueue 移除」的措辞）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261114183618.56111-1-kayracizmeci@gmail.com/
