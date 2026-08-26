---
id: sched-20260826-009
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: unknown
lore_url: unknown
authors:
- Shubhang Kaushik
maintainers_involved:
- Zhan Xusheng
current_version: v1
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-26
  summary: 修复 same-task repick 后 hrtick 未重新设置的问题
  review_outcome: Zhan Xusheng 指出 delayed dequeue 条件缺陷和设计冗余
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - delayed dequeue 条件需修正
  - rq 字段冗余需解释
  next_action: 作者回应 review 意见并发 v2
contribution_opportunities:
- kind: testing
  description: 用 ftrace 验证 delayed dequeue 场景下 h_nr_runnable != h_nr_queued 的频率
generated_at: '2026-08-27T01:26:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- sched_clock
title: 'sched/fair: Restart hrtick after same-task repicks'
layout: article
---

## TL;DR

Shubhang Kaushik (Ampere) 提交补丁修复 same-task repick 后 hrtick 未重新设置的问题。当 `pick_next_task_fair()` 选择同一任务时（例如经过 `put_prev_task` + `pick_next_task` 循环），已有的 hrtick 定时器可能未被重新设置，导致该任务的调度时间片不受 hrtick 约束。Zhan Xusheng 提出了详细的 review 意见，指出 `h_nr_runnable == h_nr_queued` 条件在 delayed dequeue 场景下会错误地关闭修复。

## 背景与问题

`task_tick_fair()` 在 `cfs_rq->curr` 变化时调用 `hrtick_start_fair()` 重新设置高精度定时器。但当 same-task repick 发生时（put + pick 选到同一任务），`curr` 未变化，hrtick 不会被重新设置。如果之前的 hrtick 已经过期或被取消，任务可能运行超过其时间片。

## 技术方案

补丁在 `put_prev_set_next_task()` 中添加逻辑：当 prev == next（same-task repick）时，显式调用 `__hrtick_rearm_fair()` 重新设置 hrtick。使用 `rq->hrtick_rearm_fair` 字段控制是否启用该修复，条件为 `hrtick_enabled_fair(rq) && h_nr_runnable > 1 && h_nr_runnable == h_nr_queued`。

## 版本演进与当前进展

v1 刚发出。Zhan Xusheng 提出了详细的 review 意见：

1. `h_nr_runnable == h_nr_queued` 条件在 delayed dequeue 场景下为 false（`set_delayed()` 递减 `h_nr_runnable` 但不影响 `h_nr_queued`），导致修复被错误关闭
2. `rq->hrtick_rearm_fair` 字段可能不必要——`__hrtick_rearm_fair()` 已经做了充分的条件检查
3. 建议考虑直接在 `entity_tick()` → `update_curr()` → `update_deadline()` 路径中调用 `hrtick_start_fair()`，无需新字段

## Maintainer 意见与讨论焦点

Zhan Xusheng 的 review 指出了方案中的逻辑缺陷（delayed dequeue 条件）和设计冗余（不必要的 rq 字段），建议简化实现。

## 合入评估

- **likelihood**: medium（方向正确但实现需要修改）
- **blocking_issues**: delayed dequeue 条件需要修正，rq 字段冗余需要解释或移除
- **next_action**: 作者回应 review 意见并发 v2

## 效果评估

暂无性能数据。修复的是 hrtick 定时器在特定路径下未被正确设置的功能问题。

## 我可以参与的点

- 可以用 ftrace 验证 delayed dequeue 场景下 `h_nr_runnable != h_nr_queued` 的频率
- 可以测试 Zhan 建议的替代方案（直接在 `entity_tick()` 中 rearm）

## 参考链接

- lore thread: 未获取到
