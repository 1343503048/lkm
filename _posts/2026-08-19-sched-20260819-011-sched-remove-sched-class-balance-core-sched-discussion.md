---
id: sched-20260819-011
date: 2026-08-19
subsystem: sched
type: feature
status: under_review
severity: low
thread_root_msgid: <unknown>
lore_url: 未获取到
authors:
- unknown
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <unknown>
  date: unknown
  summary: '目标系列：移除 sched_class::balance() 回调（0/2）。8/19 可见多封 Re: 该系列的回复，讨论焦点集中在与 core_sched
    的交互：在 core cookie 最终确定前做 balance 可能把任务错移到别的 core 上空等，且 core-sched 下 balance 用
    RETRY_TASK 机制存疑（参见 article 002 同日 Peter 的 core_sched 竞态分析）。注：本次抓取未拿到系列原始 cover
    letter，以下为该系列在 8/19 讨论中可确认的内容。'
  review_outcome: 8/19 回复主要为对 '在 pick 内做 balance 与 core-sched 正确性' 的质疑，尚未见到明确 ack
    或合入意向。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 与 core_sched 的交互未厘清（pick 内 balance 的 cookie 一致性、RETRY_TASK 语义）
  - 原始 cover 与作者未在本批抓取中获取，方案全貌待补
  next_action: 需作者澄清 balance() 移除后在 core-sched 下的等价处理，等待 Peter 对 core_sched 竞态的修复思路落定后再推进。
contribution_opportunities:
- kind: discussion
  description: 可帮忙分析移除 balance() 后 core-sched 路径如何保证 cookie 一致性，或提供原 cover letter
    的 lore 链接补全上下文。
generated_at: '2026-08-20T00:30:00'
source_email_count: 3
related_articles:
- sched-20260819-002
tags:
- sched/core
- load_balance
- core_sched
title: '`[PATCH 0/2] sched: Remove sched_class::balance()` 系列在 8/19 有多封回复'
layout: article
---

## TL;DR
`[PATCH 0/2] sched: Remove sched_class::balance()` 系列在 8/19 有多封回复，讨论焦点是与 core_sched 的交互正确性（在 pick 内做 balance 可能错移任务、core-sched 下 RETRY_TASK 语义存疑）。本次抓取未拿到原始 cover，方案全貌与作者待补；合入前景 medium，受同日 core_sched 竞态分析（article 002）牵连。

## 背景与问题
`sched_class::balance()` 是调度类的一个回调，系列意在移除它（0/2）。8/19 的回复把讨论引向一个更根本的问题：core_sched 场景下，在 core cookie 最终确定之前做 balance，可能把任务移动到错误的 core、随后因 pick 落在不同 core cookie 上而白等；且此前只有 fair 和 ext 用 RETRY_TASK，fair 在 core-sched 启用时绕过 newidle，所以 core-sched 下 balance 是否该作为 pick 的一部分仍存疑。

## 技术方案
原始 cover 未在本批邮件中抓到，无法确认移除后的具体等价实现。从 8/19 回复可确认：社区关注点在于保证 core-sched 下 balance 与 pick 的原子性/cookie 一致性，而非简单删除回调。

## 版本演进与当前进展
- 系列原始发出时间未抓到。
- 8/19：至少 3 封 `Re: [PATCH 0/2] sched: Remove sched_class::balance()` 回复，内容围绕 core-sched 交互质疑。
注：这 3 封回复的正文实际是 core_sched pick_task 竞态分析（Aaron Lu 报告 / Peter 回复），说明该系列的 review 已被 core_sched 正确性讨论接管。

## Maintainer 意见与讨论焦点
分歧/未决点：
- 移除 `balance()` 后，core-sched 下如何保证任务不被错移、pick 与 balance 在同一 core-wide 锁临界区内完成。
- core-sched 用 RETRY_TASK 机制是否可靠（Prateek 存疑，Peter 8/19 承认竞态真实，见 article 002）。
- 尚未见明确 ack 或 NAK，但方向性上需要先解决 core_sched 竞态才能谈合入。

## 合入评估
合入可能性 medium：系列本身为清理/重构，但被 core_sched 正确性这一未决问题牵连。需先等 Peter 对 core_sched pick_task 竞态给出可前进的修复思路（article 002），且作者需澄清移除 balance() 后的 core-sched 等价处理。

## 效果评估
暂无效果数据（重构类，且方案全貌未确认）。

## 我可以参与的点
- 提供该系列原始 cover letter 的 lore 链接以补全上下文。
- 分析移除 `balance()` 后 core-sched 路径的 cookie 一致性保证，回帖补充。

## 参考链接
- lore thread: 未获取到（需补原始 cover）
- 关联：article 002（同日 core_sched pick_task 竞态，Peter 8/19 分析）
