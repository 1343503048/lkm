---
id: sched-20261103-008
date: 2026-11-03
subject: proxy_reset_donor() warning from sched_proxy_block_task() when p is curr
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: <98e1914a51b7851253e93b2c6d756261@kernel.org>
lore_url: https://lore.kernel.org/all/98e1914a51b7851253e93b2c6d756261@kernel.org/
authors:
- Tejun Heo
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 为 sched_proxy_block_task() 补 p != curr 守卫。
contribution_opportunities:
- kind: new_patch
  description: 为 sched_proxy_block_task() 加 p != rq->curr 守卫，避免无谓 WARN。
- kind: testing
  description: 按作者配方复现并验证候选守卫。
generated_at: '2026-11-04T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- proxy_execution
title: proxy_reset_donor() warning from sched_proxy_block_task() when p is curr
layout: article
---

## TL;DR

Tejun Heo 报告 proxy execution 的一个 WARN：`sched_proxy_block_task()` 在 p 同时是 donor 时无条件调 `proxy_reset_donor()`，而后者 `WARN_ON_ONCE(rq->donor == rq->curr)` 会在 p 既是 curr 又是 donor 时触发。可在一分钟内复现，但作者称「除此之外运行中没有别的错」。报告型，暂无补丁。

## 背景与问题

`sched_proxy_block_task()` 只要 p 是 donor 就调 `proxy_reset_donor()`，不检查 p 是否同时也是 curr；`proxy_reset_donor()` 的 `WARN_ON_ONCE(rq->donor == rq->curr)` 于是触发：`WARNING: kernel/sched/core.c:3809 at proxy_reset_donor+0x129/0x140`，栈为 `sched_proxy_block_task → scx_prepare_setscheduler → __sched_setscheduler → ...`。触发场景：p 是带 `SCX_OPS_ENQ_BLOCKED` 的 sched_ext 任务，在 `__schedule()` 里阻塞于 mutex，作为 retained donor 仍 curr 且 donor 直到 pick 结束；pick 经 sched_ext dispatch 掉 rq 锁、`ops.dispatch()` 迁移另一 CPU 任务；该窗口内另一 CPU 的 `sched_setscheduler(p, SCHED_EXT)` 拿 pi_lock 与 rq 锁进入 `sched_proxy_block_task()`，此时 p 既是 curr 又是 donor。也偶经 `scx_sub_enable_workfn() → scx_prepare_task_sched_change()` 触发。作者称 pick 看到 p 已 dequeue、继续走，无进一步错误。

## 技术方案

未附补丁。作者给出稳定复现（8-CPU VM，sched_ext/for-7.4-fixes `2227a34ff7bf`）：`scx_qmap -X -s 100` + `stress-ng --cpu 4` + locktorture mutex + 一个快速在 SCHED_EXT/SCHED_OTHER 间 flip lock_torture_wr 线程的小程序。

## 版本演进与当前进展

*current_version: 报告（2026-11-03，msgid 98e1914a51b7851253e93b2c6d756261@kernel.org）*。当日无回帖。

## Maintainer 意见与讨论焦点

无表态（作者即维护者）。

## 合入评估

*likelihood=unknown*。WARN 本身「无其它错误」，严重度低；但暴露了 `sched_proxy_block_task()` 未区分 p==curr 的边界。*next_action*：作者可补 `p != curr`（或等价条件）的守卫避免无谓 WARN。

## 效果评估

作者给出一分钟内稳定复现的环境配方；无性能数据，WARN 之外未观察到功能异常。

## 我可以参与的点

- new_patch：为 `sched_proxy_block_task()` 加 `p != rq->curr`（或等价）守卫，避免 p 同时为 curr 与 donor 时触发 WARN。
- testing：按作者配方复现并验证候选守卫。

## 参考链接

- lore thread: https://lore.kernel.org/all/98e1914a51b7851253e93b2c6d756261@kernel.org/
