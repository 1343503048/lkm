---
id: sched-20260929-005
date: '2026-09-29'
subject: 'sched: set TIF_NEED_RESCHED before calling __trace_set_need_resched()'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260630084750.2792851-1-rhkrqnwk98@gmail.com>
lore_url: https://lore.kernel.org/all/20260630084750.2792851-1-rhkrqnwk98@gmail.com/
authors:
- Sechang
maintainers_involved:
- Andrea Righi
current_version: v3
patch_series:
- version: v3
  msgid: <20260630084750.2792851-1-rhkrqnwk98@gmail.com>
  date: null
  summary: 把 TIF_NEED_RESCHED 设置提前到 __trace_set_need_resched() 之前（v3 正文不在本日缓存）
  review_outcome: Andrea 复现 nrp monitor 违规并给 fold-in；Gabriele 担心破坏 sts monitor、倾向放宽竞态
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Andrea 与 Gabriele 的修法分歧待裁决
  - 作者尚未回复
  next_action: 作者回应 fold-in 或放宽竞态两条建议后定 v4
contribution_opportunities:
- kind: review
  description: 辨析移动 sched_entry 打点对 sts/nrp 两个 RV monitor 状态机的影响
- kind: discussion
  description: 回应 Gabriele 关于 sched_entry_preempt 放宽竞态的语义是否成立
generated_at: '2026-09-30T01:15:00'
source_email_count: 2
related_articles: []
tags:
- sched_debug
- preempt
title: 'sched: set TIF_NEED_RESCHED before calling __trace_set_need_resched()'
layout: article
---

> **subject**：`sched: set TIF_NEED_RESCHED before calling __trace_set_need_resched()`

## TL;DR

一枚关于 `sched_entry_tp`/`__trace_set_need_resched()` 与 `TIF_NEED_RESCHED` 设置顺序的 tracepoint 修复（v3，作者 Sechang）在本日重获讨论：Andrea Righi 复现出该顺序竞态会导致 runtime verification 的 nrp monitor 状态机违规，并给出把 `trace_sched_entry_tp()` 移到 `rq_lock()` 之后的 fold-in 修法；Gabriele Monaco 则担心这一移动会破坏另一侧的 sts monitor（它期望 sched_entry 在关中断之前），建议若只为修 nrp 就先放宽该竞态而非移动打点。

## 背景与问题

`__trace_set_need_resched()` 的 tracepoint 与 `TIF_NEED_RESCHED` 标志的设置顺序存在竞态：远程 CPU 在 rq->lock 下设置 `TIF_NEED_RESCHED`，但目标 CPU 可能在取得该锁之前就打出 `sched_entry_tp()`，于是 need-resched tracepoint 晚于 sched_entry。这会让 runtime verification（RV）的 nrp monitor 观测到不一致的事件序列。本补丁（作者 Sechang）的思路是把 `TIF_NEED_RESCHED` 的设置放到 `__trace_set_need_resched()` 之前。v3 正文本身不在本日缓存（线程根 msgid 时间戳显示其为早期发出的版本），本日只有两条回复。

## 技术方案

- **Andrea Righi**（09-29）指出该顺序仍留下 v2 讨论中 Prateek 描述过的竞态，并给出 fold-in：把 `__schedule()` 里的 `trace_sched_entry_tp(sched_mode == SM_PREEMPT)` 从函数开头移到 `rq_lock(rq, &rf); smp_mb__after_spinlock();` **之后**，使 sched_entry 与 TIF_NEED_RESCHED 的设置顺序一致。他复现：300 次 `perf bench sched messaging -g 20 -l 100` 下 RV nrp monitor 报 `schedule_entry_preempt on state any_thread_running`；应用该 fold-in 后 300 次通过。
- **Gabriele Monaco** 的顾虑：把 sched_entry 移到关中断之后会破坏 sts monitor（它期望 sched_entry 在 disable interrupt 之前出现）。他建议：如果这个改动只是为了修 nrp，不如**允许这个竞态**（nrp 本来就在中断上允许该竞态）——例如允许 `sched_entry_preempt` 在 need_resched 未设置时出现、但保证在 sched_exit 之前会设置。他倾向先别移动打点，等他看清 RV 模型哪种更好。

## 版本演进与当前进展

v3（作者 Sechang，完整姓名与发送日期不在本日缓存，仅 Andrea 回帖问候「Hi Sechang」可得）。早期版本不在本次分析窗口内。本日两条回复推进了「是否移动 sched_entry 打点」的讨论，作者尚未回复。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（sched_ext 维护者）：给出了可复现的 nrp monitor 违规（300 次复现 + fold-in 后通过），并请作者若同意就把 fold-in 折进 v4。
- **Gabriele Monaco**（RV/tracepoint 作者，非维护者）：反对为修 nrp 而移动打点、破坏 sts monitor；倾向放宽竞态或等 RV 模型收敛后再定。
- 分歧点：是「移动 sched_entry 打点位置」（Andrea）还是「放宽 nrp 竞态语义」（Gabriele）——尚无裁决，作者未表态。

## 合入评估

*likelihood=unknown*。方向（修 tracepoint/need_resched 顺序）无反对，但「怎么修」存在两条分歧路线、且作者尚未回应；本补丁本体不在缓存、无法判断 v3 当前实现与两条建议的关系。*blocking_issues*：Andrea 与 Gabriele 的修法分歧待裁决；作者未回复。*next_action*：作者回应两条建议（是否 fold-in Andrea 的移动、或采纳 Gabriele 的放宽竞态），再定 v4。

## 效果评估

无性能数据；正确性证据为 Andrea 的 RV nrp monitor 复现（300 次违规 → fold-in 后 300 次通过）。

## 我可以参与的点

- `review`：辨析「移动 sched_entry 打点」对 sts/nrp 两个 RV monitor 状态机的影响，判断哪条路线兼容性更好。
- `discussion`：若熟悉 RV tracepoint 语义，可回应 Gabriele 的「sched_entry_preempt 允许在 need_resched 未置位但 sched_exit 前必置位」这一放宽是否成立。

## 参考链接

- lore（v3 线程根）: https://lore.kernel.org/all/20260630084750.2792851-1-rhkrqnwk98@gmail.com/
- Andrea Righi 回复: https://lore.kernel.org/all/arqhnt6lW8qiCo19@gpd4/
- Gabriele Monaco 回复: https://lore.kernel.org/all/96b3b5d5ec0eae499f1a98845720776b6fab84d4.camel@redhat.com/
