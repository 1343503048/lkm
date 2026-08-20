---
id: sched-20260730-010
date: 2026-07-30
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: <2d191aead79140de43022f480c3b542c101613f...>
lore_url: https://lore.kernel.org/lkml/sched-cache-task-cache-work-v8
authors:
- Luo Gengkun
maintainers_involved:
- Tim Chen
current_version: v8
patch_series:
- version: v8
  msgid: <sched-cache-task-cache-work-v8...>
  date: 2026-07-29
  summary: v8 of task_cache_work optimization, only scan visited CPUs
  review_outcome: Luo Gengkun identifies epoch race condition in lockless check
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Epoch race condition needs fix before merge
  next_action: Fix the epoch backwards movement race
contribution_opportunities:
- kind: review
  description: Review the proposed fix for epoch race condition
generated_at: '2026-07-31T00:10:00'
source_email_count: 3
related_articles:
- sched-20260729-005
tags:
- cfs
- perf
title: ': [PATCH v8 1/2] sched/cache: Reduce the overhead of task_cache_work by only
  scan the visisted cpus'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 sched-20260729-005。Luo Gengkun 在 review v8 时发现 `task_tick_cache()` 中 epoch 更新的竞态条件：lockless check 在 spinlock 保护之外，可能导致 epoch 回退。Tim Chen 也参与了讨论。

## 背景与问题

`task_tick_cache()` 中的 epoch 更新逻辑：
```c
/* avoid moving backwards */
if (time_after_eq(mm->sc_stat.epoch, epoch))
    return;

guard(raw_spinlock)(&mm->sc_stat.lock);

if (work->next == work) {
    task_work_add(p, work, TWA_RESUME);
    WRITE_ONCE(mm->sc_stat.epoch, epoch);
}
```

问题：`time_after_eq()` check 在 spinlock 外执行，两个 thread 可能同时通过 check，但后获取锁的 thread 可能写入更小的 epoch 值，导致 epoch 回退。

## 技术方案

Luo Gengkun 提出的竞态场景：
- Thread A 读 rq->cpu_epoch = 100，通过 lockless check
- Thread B 读 rq->cpu_epoch = 101，通过 lockless check
- Thread B 先获取锁，写入 epoch = 101
- Thread A 获取锁，写入 epoch = 100（回退！）

解决方案：将 epoch 验证移入 spinlock 保护范围内。

## 版本演进与当前进展

- v8 (2026-07-29): 当前版本
- 2026-07-30: Luo Gengkun 发现 epoch race condition
- Tim Chen 参与讨论

## Maintainer 意见与讨论焦点

- Luo Gengkun: 详细分析了竞态条件，提出修复方向
- Tim Chen: 参与讨论

## 合入评估

- **likelihood**: unknown
- 需要先修复 epoch race condition
- 可能需要 v9

## 效果评估

暂无新的性能数据。

## 我可以参与的点

- **Review 修复方案**：等待作者提出具体修复后，可以 review epoch race condition 的修复
- 如果有高并发场景，可以测试验证修复是否消除竞态

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
- related: sched-20260729-005
