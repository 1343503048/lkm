---
id: sched-20261012-020
date: '2026-10-12'
subject: 'sched: Add task enqueue/dequeue trace points'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261001152042.124445-1-gmonaco@redhat.com>
lore_url: https://lore.kernel.org/all/20261001152042.124445-1-gmonaco@redhat.com/
authors:
- Gabriele Monaco
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261001152042.124445-1-gmonaco@redhat.com>
  date: '2026-10-01'
  summary: 在 enqueue/dequeue 路径加 sched_enqueue/sched_dequeue tracepoint
  review_outcome: 当日 Peter 在工具侧发牢骚，无实质代码 review
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 当日无实质代码 review（Peter 仅在工具/格式侧表态）
  next_action: 继续等实质性 review
contribution_opportunities: []
generated_at: '2026-10-13T01:40:00'
source_email_count: 2
related_articles:
- sched-20261003-002
- sched-20261004-005
tags:
- sched_debug
title: 'sched: Add task enqueue/dequeue trace points'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-002-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261003-002</a> / 20261004-005：Gabriele Monaco（Red Hat）在 20 补丁 RFC 中首发 tracepoint 补丁——通用 `enqueue_task()`/`dequeue_task()` 路径加 `sched_enqueue`/`sched_dequeue` tracepoint，方向由 Peter Zijlstra 建议、K Prateek Nayak 已 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-020-sched-add-task-enqueue-dequeue-trace-points.html">sched-20261012-020</a>（今天）：Peter 在该线程的两条回帖都属工具/格式侧牢骚（反感网页工具、「必须用鼠标」、抱怨新东西没让生活变好却变糟），无针对 tracepoint 代码本身的实质反馈。

## 背景与问题

（承接 20261003-002/20261004-005）为调度器 enqueue/dequeue 提供通用 tracepoint，便于观测任务进出队列。今日无新的技术背景补充。

## 技术方案

（承接 20261003-002/20261004-005）方案维持不变；今日讨论偏离到「trace 可视化工具」的取舍上（Peter 个人强烈偏好文本/终端，反感网页 UI），未触及补丁实现。

## 版本演进与当前进展

v2（10-01）→ 今日（10-12）Peter 在侧线讨论工具观感；无版本推进。

## Maintainer 意见与讨论焦点

Peter Zijlstra 今日两条回帖均为工具观感（「web SUCKS」「要动鼠标」「新东西没让生活变好却变糟」），未对该 tracepoint 补丁本身给技术意见；应视为侧线情绪表态，非 NAK。

## 合入评估

*likelihood=unknown*。当日无实质 review 进展。*blocking_issues*：实质性 review 缺位。*next_action*：等 Peter 或他人回到代码本身。

## 效果评估

无性能数字；tracepoint 补丁此前已有 K Prateek 的 Reviewed-by（见 related），今日无新数据。

## 我可以参与的点

当日无实质技术讨论，暂无明显参与空间，持续观察后续版本。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20261001152042.124445-1-gmonaco@redhat.com/
- lore（Peter 工具侧表态）: https://lore.kernel.org/all/20261012115430.GD2823843@noisy.programming.kicks-ass.net/
