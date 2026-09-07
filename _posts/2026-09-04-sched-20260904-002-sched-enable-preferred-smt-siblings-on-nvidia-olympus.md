---
id: sched-20260904-002
date: '2026-09-04'
subject: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+Enable+preferred+SMT+siblings+on+NVIDIA+Olympus
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260903-009
tags:
- sched/fair
- topology
- affinity
title: 'sched: Enable preferred SMT siblings on NVIDIA Olympus'
layout: article
---

## TL;DR

NVIDIA Olympus 以两个对称 PE 实现 SMT：仅一个 PE 活跃时核为单线程模式、可用全部资源。目前作者 Andrea Righi，v2；本日收到复审（Re 78724）。- 与 09-03 009（非对称 SMT 优先级）同源演进。

## 背景与问题

NVIDIA Olympus 以两个对称 PE 实现 SMT：仅一个 PE 活跃时核为单线程模式、可用全部资源；两个 PE 活跃则共享资源。且 sibling 空闲后从双线程回到单线程模式并非即时。本系列（v2，含封面 79146 + 2/2 "Honor asymmetric SMT priority in idle selection"）让空闲 CPU 选择尊重 `SD_ASYM_PACKING`，优先把任务放到更优 SMT 兄弟，避免短暂激活空闲兄弟造成的持久性能损失。

## 技术方案

- v2 增加封面并整合为 2 补丁系列。
- 空闲 CPU 选择考虑 `SD_ASYM_PACKING` 顺序，优先放置在更优的 SMT 兄弟线程。

## 版本演进与当前进展

- 作者 Andrea Righi，v2；本日收到复审（Re 78724）。
- 与 09-03 009（非对称 SMT 优先级）同源演进。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260903-009]] sched/fair 空闲选择尊重非对称 SMT 优先级（初版）。
- 相关代码/commit：
  - `kernel/sched/fair.c` `select_idle_sibling()` / `SD_ASYM_PACKING`
