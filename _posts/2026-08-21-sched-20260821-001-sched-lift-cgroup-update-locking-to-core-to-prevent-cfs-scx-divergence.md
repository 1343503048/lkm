---
id: sched-20260821-001
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260820160956.910663-1-michalblk@google.com>
lore_url: https://lore.kernel.org/lkml/20260821140818.1559100-1-michalblk@google.com/
authors:
- Michal Blaszczyk
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v1
  msgid: <20260820160956.910663-1-michalblk@google.com>
  date: 2026-08-20
  summary: 引入新全局 mutex 串行化 cgroup 更新
  review_outcome: PeterZ 建议复用已有 CFS 锁而非引入新锁
- version: v2
  msgid: <20260821140818.1559100-1-michalblk@google.com>
  date: 2026-08-21
  summary: 将 CFS 已有锁提升到 core 层，确保 CFS/SCX 回调原子执行
  review_outcome: PeterZ 认可方向
upstream_commit: null
fixes_commit: '819513666966'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 PeterZ 正式 ack
contribution_opportunities:
- kind: testing
  description: 在 SCX 场景下测试并发 cgroup 写入验证修复
generated_at: '2026-08-21T10:00:00'
source_email_count: 3
related_articles: []
tags:
- sched/core
- sched_ext
- cgroup
- race_condition
title: 并发写入 cgroup 控制文件（如 cpu.shares/cpu.weight）会导致 CFS 与 SCX 之间的状态不一致
layout: article
---

## TL;DR

并发写入 cgroup 控制文件（如 cpu.shares/cpu.weight）会导致 CFS 与 SCX 之间的状态不一致。v2 方案将 CFS 锁提升到 core 层，让 CFS 和 SCX 回调在同一把锁下原子执行，PeterZ 已认可方向。

## 背景与问题

`cpu_shares_write_u64()` 中 CFS 的更新由 `shares_mutex`（fair.c 内部）串行化，但这把锁在调用 `scx_group_set_weight()` 之前就被释放了。后者只持有读信号量 `scx_cgroup_ops_rwsem`，允许多个线程并发执行 SCX 更新。

这个串行化缺口导致并发写入交错执行，CFS 记录值、SCX 内部簿记（如 `tg->scx.weight`）和 BPF 调度器可能操作完全不同的参数值。类似竞态也存在于 `tg_set_bandwidth()`、`cpu_idle_write_s64()`、`cpu_weight_write_u64()` 和 `cpu_weight_nice_write_s64()` 中。

## 技术方案

v2 方案将 CFS 已有的锁（`shares_mutex`、`cfs_constraints_mutex` 等）提升到 `kernel/sched/core.c` 的核心层写处理函数中。这样 CFS 和 SCX 回调在同一把锁下原子执行，消除了竞态窗口。

v1 原本引入了一把新的全局 mutex，v2 改为复用已有 CFS 锁，更加简洁。

## 版本演进与当前进展

- **v1**（2026-08-20）：引入新全局 mutex 串行化 cgroup 更新
- **v2**（2026-08-21）：改为提升已有 CFS 锁到 core 层，避免引入额外锁

## Maintainer 意见与讨论焦点

Peter Zijlstra 明确认可："Yeah, makes sense, no point in fair having an extra/superfluous layer of locking if it is (also) needed in core."

无争议点，方向一致认可。

## 合入评估

- **likelihood**: high
- **blocking_issues**: 无
- **next_action**: 等待 PeterZ 正式 ack 后可能进入 tip/sched/core

Fixes 标签指向 `819513666966 ("sched_ext: Add cgroup support")`，属于对已有 SCX cgroup 支持的修复。

## 效果评估

暂无性能数据，修复的是并发竞态问题，效果体现在正确性而非性能。

## 我可以参与的点

- 在 SCX 调度器场景下测试并发 cgroup 写入（多线程同时修改 cpu.weight/cpu.shares），验证修复是否彻底
- 检查是否还有其他 cgroup 写路径存在类似串行化缺口

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821140818.1559100-1-michalblk@google.com/
- lore thread (v1): https://lore.kernel.org/lkml/20260820160956.910663-1-michalblk@google.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
