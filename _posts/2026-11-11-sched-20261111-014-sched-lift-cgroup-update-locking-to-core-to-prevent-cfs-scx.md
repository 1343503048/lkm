---
id: sched-20261111-014
date: '2026-11-11'
subject: 'sched: Lift cgroup update locking to core to prevent CFS/SCX divergence'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261110151857.1864222-1-michalblk@google.com>
lore_url: https://lore.kernel.org/all/20261110151857.1864222-1-michalblk@google.com/
authors:
- Michal Blaszczyk
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
- Andrea Righi
current_version: v3
patch_series:
- version: v3
  msgid: <20261110151857.1864222-1-michalblk@google.com>
  date: '2026-11-10'
  summary: CFS 锁上移到 core 层，CFS 与 SCX 回调同锁原子执行
  review_outcome: Andrea R-b、Tejun Ack，Peter 今日回复 Thanks
upstream_commit: null
fixes_commit: '819513666966'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Peter 收取并合入 tip/sched/core
contribution_opportunities:
- kind: testing
  description: 在带 SCX 调度器场景并发压测 cpu.weight/idle/max 写验证无分歧
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261110-001
tags:
- cgroup
- cfs
- sched_ext
title: 'sched: Lift cgroup update locking to core to prevent CFS/SCX divergence'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-001-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx.html">sched-20261110-001</a>：Michal Blaszczyk 发 v3 RESEND——并发写 cgroup 控制文件（`cpu.shares`/`cpu.weight`/`cpu.max` 等）时，CFS 与 SCX 的状态更新不是原子的：CFS 部分由 `shares_mutex` 串行化但在调用 `scx_group_set_weight()` 前已释放，导致 CFS、SCX 内部记账（`tg->scx.weight`）与 BPF 调度器三者看到互不一致的参数。修复把 CFS 的锁上移到 `kernel/sched/core.c`，让 CFS 与 SCX 回调在同一把锁下原子执行。已有 Andrea Righi 的 Reviewed-by、Tejun Heo 的 Acked-by。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-014-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx.html">sched-20261111-014</a>（今天）：**Peter Zijlstra 简短回复「Thanks!」**——结合 Peter 在 v1 阶段就认可「把锁上移到 core」的方向、以及 Tejun 的 Acked-by，这一回应可视为 Peter 已接受该补丁，系列进入收取/合入前的最后阶段。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-001-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx.html">sched-20261110-001</a>）对 cgroup 控制文件的并发写会在 CFS 与 SCX 之间制造状态分歧。以 `cpu_shares_write_u64()` 为例：CFS 更新由 `shares_mutex`（fair.c 内部）串行化，但该锁在调用 `scx_group_set_weight()` 之前释放；`scx_group_set_weight()` 只拿读信号量 `scx_cgroup_ops_rwsem`，允许多线程并发评估执行 sched_ext 更新。同类竞态还存在于 `tg_set_bandwidth()`、`cpu_idle_write_s64()`、`cpu_weight_write_u64()`、`cpu_weight_nice_write_s64()`。`Fixes: 819513666966 ("sched_ext: Add cgroup support")`。

## 技术方案

（承接 v3，无变化）把 CFS 的锁上移到 core 层：新增全局 `DEFINE_MUTEX(cpu_weight_mutex)` 替换 fair.c 内部原锁，在 `cpu_shares_write_u64()` 等核心写回处理器里用 `guard(mutex)(&cpu_weight_mutex)` 同时包裹 `sched_group_set_shares_locked()` 与 `scx_group_set_weight()`，同类写回一并处理。改动 `kernel/sched/core.c`/`fair.c`/`sched.h` 共 +43/-24。

## 版本演进与当前进展

*current_version: v3（RESEND，2026-11-10，`<20261110151857.1864222-1-michalblk@google.com>`）*。RESEND 相对 v3 无改动，仅 rebase 到 tip/sched/core 并补上 Andrea R-b 与 Tejun Ack。今日 Peter 回复「Thanks!」，无新版本。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched 维护者）**：今日回复「Thanks!」，结合其 v1 阶段「认可把锁上移到 core 层」的既有表态，可视为接受补丁。
- **Tejun Heo（sched_ext 维护者）**：Acked-by。
- **Andrea Righi（sched_ext 维护者）**：Reviewed-by。
- 无 NAK、无未解决争议。

## 合入评估

*likelihood=high*。Peter 今日已回应，方向自 v1 起获认可、Tejun/Andrea 均已背书，作者做过 lockdep/分裂复测。*blocking_issues*：无实质阻塞。*next_action*：Peter 收取并合入 tip/sched/core（或给出「已应用」的确认）。

## 效果评估

作者此前给出确定性复现：BPF 调度器在 `ops.cgroup_set_*` 中自旋 5ms 时，打补丁前 30/30 轮出现分歧、打补丁后 0/30。正确性修复，无性能数据。

## 我可以参与的点

- **testing**：在带 SCX 调度器的场景并发压测 `cpu.weight`/`cpu.idle`/`cpu.max` 写，验证无分歧与无 lockdep 告警。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110151857.1864222-1-michalblk@google.com/
- Peter 的回应: https://lore.kernel.org/all/20261111094256.GY2668804@noisy.programming.kicks-ass.net/
