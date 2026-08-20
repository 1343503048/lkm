---
subject: 'sched/core: Make core-sched flips wait for in-flight selections'
id: sched-20260810-006
date: 2026-08-10
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260809164109.xxxxxx-tejun@kernel.org>
lore_url: 未获取到
authors:
- Tejun Heo
maintainers_involved:
- Peter Zijlstra
- Joel Fernandes
- Ingo Molnar
- Juri Lelli
current_version: v1
patch_series:
- version: v1
  msgid: <20260809164109.xxxxxx-tejun@kernel.org>
  date: 2026-08-09
  summary: 6 patches 系列：core-sched 翻转（core-sched flips）等待在途选择完成，并处理 pick_task() 释放
    rq 锁的竞态。
  review_outcome: Peter 在 PATCH 1/6（Handle pick_task() releasing rq lock）与 PATCH 2/6（Make
    core-sched flips wait for in-flight selections）给出详细反馈与修改建议。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 指出 pick_task() 释放 rq 锁的竞态处理需重新设计
  next_action: 作者根据 Peter 的 1/6、2/6 反馈修订后重新提交。
contribution_opportunities:
- kind: review
  description: 评审 pick_task() 释放 rq 锁后的 core-sched 选择一致性处理。
- kind: discussion
  description: 参与 core-sched 翻转等待在途选择的设计讨论。
generated_at: '2026-08-11T00:15:00'
source_email_count: 3
related_articles: []
tags:
- core_sched
- sched/core
title: 'sched/core: Make core-sched flips wait for in-flight selections'
layout: article
---

## TL;DR
Tejun Heo 提交 6-patch core-sched 稳定性系列（core-sched flips 等待在途选择、pick_task() 释放 rq 锁的竞态处理）。Peter 在 PATCH 1/6、2/6 给出详细反馈。under_review。

## 背景与问题
core scheduling 在 SMT 兄弟线程间需做「core 级」任务选择（cookie 匹配）。两个问题：
1. core-sched flips（core 调度状态翻转）可能在已有在途选择未完成时触发，造成状态不一致；
2. `pick_task()` 在 core 选择过程中可能释放 rq 锁，导致另一端 CPU 看到不一致的中间状态。

## 技术方案
- 让 core-sched flips 等待所有在途选择完成后再翻转状态；
- 处理 `pick_task()` 释放 rq 锁的窗口：在释放/重取锁后重新校验选择前提，避免基于陈旧状态做决定。具体实现以 6-patch 系列为准。

## 版本演进与当前进展
当前 v1（6 patches）。Peter 于 8/10 在 1/6、2/6 给出修改建议，作者预计修订。

## Maintainer 意见与讨论焦点
Peter 明确指出 PATCH 1/6 的 rq 锁释放竞态处理需要重新设计，PATCH 2/6 的等待语义需更清晰。这是当前主要阻塞点。

## 合入评估
合入可能性 medium。方向对，但需按 Peter 反馈修订；core-sched 路径正确性要求高。

## 效果评估
无 benchmark；修复 core-sched 在并发翻转/锁释放窗口下的正确性。

## 我可以参与的点
- 评审 pick_task() 锁释放窗口的正确性证明；
- 在开启 SCHED_CORE 的内核上做并发 core-sched 翻转压力测试。

## 参考链接
- lore: 未获取到
