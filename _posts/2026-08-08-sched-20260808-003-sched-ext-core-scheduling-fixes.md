---
subject: 'sched_ext: 修复 core scheduling 下的 rq 锁释放与 core_pick 损坏'
date: 2026-08-08
series: sched-ext-core-scheduling-fixes
version: v1
status: in-review
tags:
- sched_ext
- core_sched
related_articles: []
submitter: Tejun Heo
emails:
- uid: 27703
  subject: '[PATCHSET sched_ext/for-7.2-fixes] sched_ext: Fix core scheduling'
- uid: 27687
  subject: '[PATCH 1/6] sched/core: Handle pick_task() releasing the rq lock'
- uid: 27705
  subject: '[PATCH 2/6] sched/core: Make core-sched flips wait for in-flight selections'
- uid: 27690
  subject: '[PATCH 3/6] sched_ext: Replace SCX_RQ_BAL_KEEP with a dispatch verdict
    return'
- uid: 27691
  subject: '[PATCH 4/6] sched_ext: Fix this_rq() assumptions in dispatch kfuncs'
- uid: 27688
  subject: '[PATCH 5/6] sched_ext: Count rq lock releases in rq->scx.lock_drop_seq'
- uid: 27689
  subject: '[PATCH 6/6] sched_ext: Fix rq->core_pick corruption under core scheduling'
title: 'sched_ext: 修复 core scheduling 下的 rq 锁释放与 core_pick 损坏'
layout: article
---

## 概述

Tejun Heo 提交 `[PATCHSET sched_ext/for-7.2-fixes]`，6 片修复 sched_ext 在 **core scheduling（核心调度，SMT 兄弟协同选择）** 下的系列回归：因 sched_ext 的 dispatch 可在 pick 期间释放 rq 锁，破坏了 core-wide 选择的原子性，导致 `rq->core_pick` 损坏。

## 问题分析

在 core scheduling 下，`pick_next_task()` 在持有一把 core-wide 共享 rq 锁的连续区间内为所有 SMT 兄弟做选择；而 sched_ext 的 dispatch 可以从 pick 内部释放那把锁。这会使 core-wide 选择失效，单个 pick 能消费到过期状态，进而损坏 `rq->core_pick`。

## 六片内容

1. **sched/core: Handle pick_task() releasing the rq lock** — 让 core-sched 的 pick 能感知 dispatch 期间发生的 rq 锁释放并重试。
2. **sched/core: Make core-sched flips wait for in-flight selections** — core-sched 的翻转（使能/禁用切换）等待在途选择完成。
3. **sched_ext: Replace SCX_RQ_BAL_KEEP with a dispatch verdict return** — `SCX_RQ_BAL_KEEP`（告诉 pick 保留上一任务）原为平衡与 pick 分离时的遗留；rq 级标志只在 dispatch 与 pick 一一配对时有效，core scheduling 打破了这一点（选择经 dispatch 的锁释放交错，pick 可消费过期标志保留已被出队的任务）。改为让 `scx_dispatch_sched()` 与 `balance_one()` 返回显式 verdict，使"保留/迁移"决策随 dispatch 一起传递。
4. **sched_ext: Fix this_rq() assumptions in dispatch kfuncs** — 修正 dispatch kfunc 中对 `this_rq()` 的假设（锁释放后 this_rq 可能变化）。
5. **sched_ext: Count rq lock releases in rq->scx.lock_drop_seq** — 新增 `rq->scx.lock_drop_seq` 计数器，在每次"dispatch 可能在途时释放 rq 锁"的站点自增（仅在 core scheduling 启用时维护），供 core-sched pick 判断期间是否发生过释放。Fixes `4c95380701f5`（"sched/ext: Fold balance_scx() into pick_task_scx()"），标记 `Cc: stable@vger.kernel.org # v6.19+`。
6. **sched_ext: Fix rq->core_pick corruption under core scheduling** — 最终修复 `rq->core_pick` 损坏。

## 状态

提交到 `sched_ext/for-7.2-fixes`，标注 stable（v6.19+），处于评审阶段。

## 参考链接

- 系列：uid 27703 / 27687 / 27705 / 27690 / 27691 / 27688 / 27689
