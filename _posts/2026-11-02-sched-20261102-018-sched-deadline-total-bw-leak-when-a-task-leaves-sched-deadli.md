---
type: bug
status: under_review
severity: high
thread_root_msgid: <2b5fb3f22bca6aa383be8f4781923392@kernel.org>
authors:
- Tejun Heo
maintainers_involved:
- Juri Lelli
current_version: null
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - KEEP_PARAMS 负扣与 offline 除零两边界待并案修复
  next_action: Tejun 重测 Juri 分支；Juri 一并处理两边界后正式提交
contribution_opportunities:
- kind: testing
  description: 重测 KEEP_PARAMS 与 offline-crash 边界
- kind: review
  description: 审阅 fail-early 与 __dl_sub 除零防护
upstream_commit: null
fixes_commit: null
merged_branch: null
source_email_count: 2
related_articles:
- sched-20261030-001
- sched-20261031-011
tags:
- deadline
id: sched-20261102-018
subject: 'sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not
  queued'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched/deadline: total_bw leak when a task leaves SCHED_DEADLINE while not
  queued'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-001-sched-deadline-total-bw-leak-when-a-task-leaves-sched-deadli.html">sched-20261030-001</a>：Tejun Heo 报告未入队 SCHED_DEADLINE 任务切策略不归还 total_bw，Juri 当日给 inline 修复。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-011-sched-deadline-total-bw-leak-when-a-task-leaves-sched-deadli.html">sched-20261031-011</a>：Tejun 实测 Juri 补丁——基本泄漏修好，但暴露 `KEEP_PARAMS` 反复切换把 total_bw 扣成负数、及「CPU 下线后切走睡眠 DEADLINE」在 `__dl_sub()` 除以 `dl_bw_cpus()=0` Oops 两个新问题。
- sched-20261102（今天）：Juri 逐一回应——把 DEADLINE 任务 `sched_setattr(OTHER, KEEP_PARAMS)` 判为「应尽早报错拒绝」；CPU-offline 除零是「我 total_bw 修复使其变得更糟的既有问题（有修复时是 leak 不 crash）」，他准备一并处理；并请 Tejun 用其 `fix/dl-total-bw-leak` 分支重测。

## 背景与问题

（承接）DEADLINE 任务未入队切走时 total_bw 泄漏，以及 Juri 修复带来的两个边界缺陷。

## 技术方案

（承接）无新代码；Juri 给出三个问题的处置倾向：1) `OTHER+KEEP_PARAMS` 应 fail early；2) `__dl_sub()` 除零是 pre-existing、其修复放大；3) 提供 `fix/dl-total-bw-leak` 分支与 reproducer 请求回归。

## 版本演进与当前进展

Juri 的修复分支迭代中，待 Tejun 重测。

## Maintainer 意见与讨论焦点

维护者（Juri）对两个边界问题均有明确判定，未争论、进入修复合流阶段。

## 合入评估

likelihood=medium。基本泄漏已有修复，但需并案处理两个边界问题后正式提交。

## 效果评估

（承接）Tejun 前测：三种 case 泄漏归 0、60s 随机策略抖动后 total_bw 回初值。

## 我可以参与的点

- testing：用 Juri 的 reproducer/分支重测 KEEP_PARAMS 与 offline-crash 两边界。
- review：审阅 fail-early 断言与 `__dl_sub()` 除零防护的正确性。

## 参考链接

- lore thread: https://lore.kernel.org/all/2b5fb3f22bca6aa383be8f4781923392@kernel.org/
