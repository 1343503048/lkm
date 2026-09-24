---
id: sched-20260924-004
date: '2026-09-24'
subject: 'sched_ext: Avoid relocking DSQ during remote DSQ moves'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260923213444.3231509-1-usama.arif@linux.dev>
lore_url: https://lore.kernel.org/all/20260923213444.3231509-1-usama.arif@linux.dev/
authors:
- Usama Arif
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20260923213444.3231509-1-usama.arif@linux.dev>
  date: '2026-09-24'
  summary: 释放 src_dsq->lock 前调用 dispatch_dequeue_locked 避免重加锁
  review_outcome: Tejun 合入 sched_ext/for-7.4（context 调整）
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched_ext/for-7.4 进入 upstream 拉取
contribution_opportunities: []
generated_at: '2026-09-25T09:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Avoid relocking DSQ during remote DSQ moves'
layout: article
---

## TL;DR
Usama Arif 的小优化补丁：`scx_bpf_dsq_move*()` 把任务从非本地 DSQ 移到远端本地 DSQ 时，`move_task_between_dsqs()` 会先丢掉 `src_dsq->lock`（但保留 `p->scx.dsq`），随后的 `deactivate_task()` 又在 `scx_dispatch_dequeue()` 里重新获取同一把锁来 unlink。补丁在释放锁前直接调用 `dispatch_dequeue_locked()`，让后续 `deactivate_task()` 走免锁的 `!dsq` 路径，省掉一次冗余加锁。Tejun Heo 已合入 `sched_ext/for-7.4`（1 行改动）。

## 背景与问题
`scx_bpf_dsq_move()`/`scx_bpf_dsq_move_vtime()` 把任务迁移到远端本地 DSQ 时，`move_task_between_dsqs()` 的 remote 分支：

1. 源 rq 与 `src_dsq` 都已加锁后，先释放 `src_dsq->lock`，但 `p->scx.dsq` 仍指向源 DSQ；
2. 随后的 `deactivate_task()` → `scx_dispatch_dequeue()` 见到 `p->scx.dsq` 非空，为 unlink 任务并清 `p->scx.dsq` 而**重新获取**刚放掉的 `src_dsq->lock`。

这是同一次操作里的冗余二次加锁，纯开销、无正确性问题。

## 技术方案
在释放 `src_dsq->lock` 之前调用 `dispatch_dequeue_locked(p, src_dsq)`（此时锁仍持有），让任务先完成 unlink、`p->scx.dsq` 被清空，则后续 `deactivate_task()` 走 `!dsq` 免锁分支，避免重加锁。改动 1 行（kernel/sched/ext/ext.c 的 `move_task_between_dsqs()` remote 分支）。`Suggested-by: Tejun Heo`。

## 版本演进与当前进展
v1 本日发出（`<20260923213444.3231509-1-usama.arif@linux.dev>`）。Tejun Heo 回帖表示已合入 `sched_ext/for-7.4`，仅因补丁是基于 for-next 的，做了 context 调整。

## Maintainer 意见与讨论焦点
- **Tejun Heo（sched_ext 维护者）**：立即采纳并合入，仅提示 context 需从 for-next 适配。无争议、无 NAK。

## 合入评估
*likelihood=merged*。已被 sched_ext 维护者合入 `sched_ext/for-7.4`（未进 mainline/tip，故 status 记 merged_tip 语义为「已进调度器维护者分支」）。*blocking_issues*：无。*next_action*：随 `sched_ext/for-7.4` 整体进入后续 upstream 拉取。

## 效果评估
无量化数据；属微优化（消除一次热路径上的冗余 rq/DSQ 锁重获取），作者未附 benchmark。

## 我可以参与的点
当前阶段暂无明显参与空间——已合入维护者分支，可持续观察 `sched_ext/for-7.4` 的上游化进度。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260923213444.3231509-1-usama.arif@linux.dev/
- Tejun 合入回复: https://lore.kernel.org/all/c21c23f034e82b7802572050cf702865@kernel.org/
