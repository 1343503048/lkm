---
id: sched-20261105-023
date: 2026-11-05
subject: 'cpuidle: idle_miss accounting fixes'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261030083633.1699270-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20261030083633.1699270-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved:
- Rafael J. Wysocki
current_version: v1
patch_series:
- version: v1
  msgid: <20261030083633.1699270-1-christian.loehle@arm.com>
  date: 2026-10-30
  summary: 2 补丁修正 cpuidle idle_miss 记账。
  review_outcome: Rafael 初步无顾虑。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等 Rafael 完整审阅后收取
contribution_opportunities:
- kind: review
  description: 核对 idle_miss 记账在 menu/TEO 路径下的语义一致性
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- idle
title: 'cpuidle: idle_miss accounting fixes'
layout: article
---

## TL;DR

Christian Loehle 的两补丁系列修复 cpuidle 的 idle_miss 记账。今日 Loehle 追问维护者意见，Rafael J. Wysocki 回应「只粗略看过、目前没有顾虑」。方向获维护者初步认可，处于低争议的待收取状态。

## 背景与问题

cpuidle 的 idle_miss 记账存在缺陷（本窗口仅获得 cover 的追问与回复，具体缺陷细节未获取到更多邮件正文）。idle_miss 反映「governor 预测的 idle 时长与实际不符」的次数，记账不准会影响 idle 统计与后续 governor 决策评估。

## 技术方案

两补丁（0/2）修正 idle_miss 的记账逻辑；具体 diff 未在当日缓存中获取到。

## 版本演进与当前进展

*current_version: v1（2026-10-30 发出）*。今日 Loehle 追问「Rafael, any opinions?」，Rafael 回复暂无顾虑。

## Maintainer 意见与讨论焦点

Rafael J. Wysocki（cpuidle 维护者）表示只粗略看过、目前无顾虑——属积极但尚未深入审阅的信号，未给出正式 Ack。

## 合入评估

*likelihood=medium*。维护者初步无顾虑，但尚未深入审阅或 Ack。*blocking_issues*：暂无明确阻塞。*next_action*：等 Rafael 完整审阅后收取。

## 效果评估

无性能数据（记账正确性修复）。

## 我可以参与的点

- review：核对 idle_miss 记账修复在 menu/TEO 两个 governor 路径下的语义一致性。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261030083633.1699270-1-christian.loehle@arm.com/
- Rafael 回复: https://lore.kernel.org/all/CAJZ5v0hHhRYihhssF1PSqbNRKH6w_qBbWR6G1YWdJeMtAfMNbg@mail.gmail.com/
