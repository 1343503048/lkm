---
id: sched-20260930-009
date: '2026-09-30'
subject: 'sched/fair: Take slice protection into account when arming HRTICK'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260929194711.2689811-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20260929194711.2689811-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260929194711.2689811-1-christian.loehle@arm.com>
  date: '2026-09-30'
  summary: fair hrtick 取 deadline 与存活 protection 较早者定时，并在 wakeup 缩短 protection 后重算
  review_outcome: 无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review 表态
  next_action: 等 Vincent/Peter 对 HRTICK 定时点改动的 review
contribution_opportunities:
- kind: testing
  description: 在低 HZ 下跑短/长 request 等权混布负载，对比切换间隔与调度延迟
- kind: review
  description: 核对 wakeup 后重算 hrtick 的时序与 lazy reschedule 触发条件
generated_at: '2026-10-01T01:00:00'
source_email_count: 1
related_articles: []
tags:
- eevdf
- preempt
title: 'sched/fair: Take slice protection into account when arming HRTICK'
layout: article
---

> **subject**：`sched/fair: Take slice protection into account when arming HRTICK`

## TL;DR

Christian Loehle 的 EEVDF 调度粒度修复：EEVDF 会在更短 request 竞争时提前结束任务的 slice protection，`update_curr()` 在 protection 到期时请求重选，但 `hrtick_start_fair()` 仍按虚拟 deadline 定时——无中间调度事件时，下次重选机会远晚于 protection 边界。例如两个等权 SCHED_OTHER 任务（100 us 与 1 ms）在单 CPU 上，未修补的 HZ=250 内核两任务均呈现约 1 ms 的切换粒度（短 request 被反复 repick、不受单次 request 限制）。补丁让 fair hrtick 取「虚拟 deadline 与存活 protection」的较早者定时，并在 wakeup 缩短 protection 后重算。`Reported-by: Vincent Guittot`，当日无回帖。

## 背景与问题

EEVDF 中，当 runqueue 上有更短 request 竞争时，任务的 slice protection 会在其虚拟 deadline 之前结束。`update_curr()` 在 protection 到期时请求一次重选，但 `hrtick_start_fair()` 仍把定时器武装到虚拟 deadline；若中间没有其他调度事件，重新考虑该任务的机会会远晚于 protection 边界。结果：一个短 request 的任务可被反复 repick，其不受单次 request 限制地连续运行；CPU 份额仍大致相等，但调度粒度变粗（两个 100 us / 1 ms 的等权任务在 HZ=250 上呈现约 1 ms 的切换间隔）。

## 技术方案

把 fair hrtick 武装到「虚拟 deadline 与存活 slice protection」的较早者，protection 到期后回退到 deadline。same-task repick 会重启定时器但不续 protection，使新 eligible 任务无需再等一个受保护 quantum 即可竞争。此外，wakeup 可缩短 protection 而不抢占 current：enqueue 路径在 `wakeup_preempt_fair()` 更新 protection 之前就调了 `hrtick_update()`，而后者对已激活的定时器不作处理——因此在 `update_protect_slice()` 改变 vprot 后重算 fair hrtick（含已激活定时器），若新 protection 边界已过则请求 lazy reschedule（与 `update_curr()` 在 protection 到期时的行为一致），而非回退到更晚的 deadline。

## 版本演进与当前进展

v1 刚发出（`<20260929194711.2689811-1-christian.loehle@arm.com>`）。当日无回帖。

## Maintainer 意见与讨论焦点

当日无回帖。`Reported-by: Vincent Guittot`（链接指向其两封关于 EEVDF 调度粒度/HRTICK 的报告）。无 NAK，待 review。

## 合入评估

*likelihood=unknown*。补丁针对明确的调度粒度缺陷、给出具体复现与机制，但刚发出、无任何维护者表态，且与作者同日的「Fix slice protection across state changes」系列（<a class="article-ref" href="/lkm/2026/09/30/sched-20260930-008-sched-eevdf-fix-slice-protection-across-state-changes.html">sched-20260930-008</a>）同源，可能需要在那个系列收敛后一并评估。*blocking_issues*：无 review 表态。*next_action*：等 Vincent/Peter 对 HRTICK 定时点改动的 review。

## 效果评估

作者给出定性复现：两个等权 SCHED_OTHER 任务（100 us 与 1 ms）在单 CPU、未修补 HZ=250 内核上约 1 ms 切换一次；修补后调度粒度应收敛到 protection 边界（100 us 任务可及时让出）。无量化 benchmark 数字。

## 我可以参与的点

- `testing`：在 HZ=250（或更低 HZ）下跑「短 request + 长 request 等权混布」负载，对比补丁前后的切换间隔分布与调度延迟，验证粒度改善。
- `review`：核对「wakeup 后重算 hrtick（含已激活定时器）」的时序——在 `wakeup_preempt_fair()` 更新 protection 前后重算的竞态与 lazy reschedule 的触发条件。

## 参考链接

- lore（补丁）: https://lore.kernel.org/all/20260929194711.2689811-1-christian.loehle@arm.com/
