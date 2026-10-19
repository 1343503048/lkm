---
id: sched-20261019-010
subject: 'sched/core: Use the scheduling context for remote ticks'
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>
lore_url: https://lore.kernel.org/all/20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>
  date: 2026-10-16
  summary: sched_tick_remote() 对 rq->donor 调 task_tick()，移除 WARN_ON_ONCE(curr!=donor)，rq->curr
    仅做执行时间 sanity check
  review_outcome: Christian Loehle 给 NIT 并指向 sashiko review（见今）
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无维护者 review
  - sashiko review 意见待作者处理
  next_action: 作者处理 NIT、采纳 sashiko 意见后重发，等 nohz/proxy execution 维护者 review
contribution_opportunities:
- kind: review
  description: 核对 sashiko review 意见并验证 task_tick() 挂 donor 的语义等价性
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles:
- sched-20261017-005
tags:
- proxy_execution
- nohz
- tick
title: 'sched/core: Use the scheduling context for remote ticks'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/17/sched-20261017-005-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261017-005</a>：Shubhang Kaushik（Ampere）单补丁——full-nohz 远程 tick `sched_tick_remote()` 对 `rq->curr` 调 `task_tick()`，但 proxy execution 下 `rq->curr` 是 mutex-owner 执行上下文、`rq->donor` 才是调度上下文；改为对 `rq->donor` 调 `task_tick()` 并移除 `WARN_ON_ONCE(curr!=donor)`。带 `Fixes: 7de9d4f94638`，当日新发。
- <a class="article-ref" href="/lkm/2026/10/19/sched-20261019-010-sched-core-use-the-scheduling-context-for-remote-ticks.html">sched-20261019-010</a>（今天）：Christian Loehle（Arm）回帖一个 NIT（去掉多余空行）+「sashiko 的 review 看着靠谱，要不要一并采纳？」——指向 sashiko 对同一补丁的审查页，属正向跟进，无维护者结论。

## 背景与问题

（承接 20261017-005）proxy execution 下 `rq->curr` 与 `rq->donor` 分离：mutex 阻塞的任务仍为 proxy execution 排队，`find_proxy_task()` 把其 owner 选为 `rq->curr`、保留阻塞任务为 `rq->donor`；远程 tick 落在 `rq->curr` 上做调度记账，与真正该记账的 `rq->donor` 不一致，且原 `WARN_ON_ONCE(rq->curr != rq->donor)` 假设被 proxy execution 打破。

## 技术方案

（承接 20261017-005）今日无新补丁，为 review 反馈：Christian 提了一个排版 NIT（两行间多余空行），并指出 sashiko 对该补丁的审查页（`sashiko.dev/#/patchset/...`）里有意见值得一并处理。原方案本身（`task_tick()` 改挂 `rq->donor`、`rq->curr` 仅做执行时间 sanity check）未被动摇。

## 版本演进与当前进展

*current_version: v1*。今日 Christian Loehle 给出 NIT + 指向 sashiko review，作者尚未回复。

## Maintainer 意见与讨论焦点

Christian Loehle（Arm，资深 reviewer，非维护者）：「sashiko 的 review 看着合理，要不要采纳？」，并给一个排版 NIT。sashiko review 的具体内容需点进链接查看（邮件正文未附结论）。proxy execution / nohz 维护者仍未表态。

## 合入评估

*likelihood=unknown*。改动小而语义清晰，但仅获 reviewer 级 NIT 与第三方（sashiko）review 指引，无维护者 ack。*blocking_issues*：无维护者 review、sashiko review 意见待作者处理。*next_action*：作者处理 NIT、评估并采纳 sashiko review 意见后重发，等 nohz/proxy execution 维护者 review。

## 效果评估

（承接 20261017-005）作者此前在 Ampere Altra + `CONFIG_SCHED_PROXY_EXEC=y` + `nohz_full=78` + RT boosting 复现 `WARN_ON_ONCE`，补丁后 10 分钟负载无 scheduler WARNING。今日无新增数据。

## 我可以参与的点

- `review`：查看 sashiko review 页并核对其意见是否成立，帮助作者收敛（`task_tick()` 挂 donor 的语义等价性仍是核心待证点）。

## 参考链接

- Christian 回帖：https://lore.kernel.org/all/a6c27dc2-ea8b-4c33-8c16-088d7501f9ac@arm.com/
- sashiko review：https://sashiko.dev/#/patchset/20261016-remote-tick-proxy-v1-1-272757a50a07%40gentwo.org
- patch：https://lore.kernel.org/all/20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org/
