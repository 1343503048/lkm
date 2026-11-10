---
id: sched-20261110-001
date: '2026-11-10'
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
- version: v1
  msgid: <20260820160956.910663-1-michalblk@google.com>
  date: '2026-08-20'
  summary: 引入全新全局 mutex 串行化 CFS/SCX cgroup 写
  review_outcome: Peter 认可把锁上移到 core 的方向
- version: v2
  msgid: <20260821140818.1559100-1-michalblk@google.com>
  date: '2026-08-21'
  summary: 改为把现有 CFS 锁上移，而非引入新锁
  review_outcome: 方向确认
- version: v3
  msgid: <20260824074913.2468177-1-michalblk@google.com>
  date: '2026-08-24'
  summary: 重命名 shares/cfs_constraints 两个互斥锁
  review_outcome: Andrea Reviewed-by，Tejun Acked-by
upstream_commit: null
fixes_commit: '819513666966'
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: Tejun/Peter 收取并合入 tip/sched/core
contribution_opportunities:
- kind: testing
  description: 在带 SCX 调度器的场景并发压测 cpu.weight/idle/max 写，验证无分歧与无 lockdep
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cgroup
- cfs
- sched_ext
title: 'sched: Lift cgroup update locking to core to prevent CFS/SCX divergence'
layout: article
---

## TL;DR

Michal Blaszczyk 发 v3 RESEND：并发写 cgroup 控制文件（`cpu.shares`/`cpu.weight`/`cpu.max` 等）时，CFS 与 SCX 的状态更新不是原子的——CFS 部分由 `shares_mutex` 串行化但在调用 `scx_group_set_weight()` 前已释放，导致 CFS、SCX 内部记账（`tg->scx.weight`）与 BPF 调度器三者看到互不一致的参数。修复把 CFS 的锁上移到 `kernel/sched/core.c` 的核心写回处理器，让 CFS 与 SCX 回调在同一把锁下原子执行。已有 Andrea Righi 的 Reviewed-by、Tejun Heo 的 Acked-by，Peter 在 v1 就认可「把锁上移到 core」的方向，等待收取。

## 背景与问题

对 cgroup 控制文件（如 `cpu.shares`、`cpu.weight`、`cpu.max`、`cpu.idle`、`cpu.weight.nice`）的并发写会在 CFS 与 SCX（sched_ext）之间制造状态分歧。以 `cpu_shares_write_u64()` 为例：CFS 部分的更新由 `shares_mutex`（fair.c 内部）串行化，但该锁在调用 `scx_group_set_weight()` 之前就被释放；而 `scx_group_set_weight()` 只拿一把读信号量 `scx_cgroup_ops_rwsem`，允许多个线程并发地评估并执行 sched_ext 更新。这个串行化缺口让并发写可以交错，最终 CFS 记录的状态、SCX 内部记账（`tg->scx.weight`）、以及 BPF 调度器本身可能各自运行在完全不同的参数上。同类竞态还存在于 `tg_set_bandwidth()`、`cpu_idle_write_s64()`、`cpu_weight_write_u64()`、`cpu_weight_nice_write_s64()`。Fix 指向 `819513666966 ("sched_ext: Add cgroup support")`。

## 技术方案

把 CFS 的锁上移到 core 层（`kernel/sched/core.c`）：在这些核心写回处理器里直接获取同一把互斥锁，使 CFS 与 SCX 回调在同一锁下原子执行。具体：新增全局 `DEFINE_MUTEX(cpu_weight_mutex)` 替换掉 fair.c 内部原来的锁，`cpu_shares_write_u64()` 里用 `guard(mutex)(&cpu_weight_mutex)` 包裹 `sched_group_set_shares_locked()` 与 `scx_group_set_weight()`；同类写回（bandwidth/idle/weight/weight_nice）一并处理。改动 `kernel/sched/core.c`（+35/-12）、`kernel/sched/fair.c`（+25/-12）、`kernel/sched/sched.h`（+7），共 3 文件 +43/-24。

v1→v3 的演进是方案本身的收敛：v1 用一个全新的全局 mutex；v2 按评审意见改为「把现有 CFS 锁上移」，避免引入新锁；v3 只是重命名 shares/cfs_constraints 两个互斥锁。

## 版本演进与当前进展

*current_version: v3（RESEND，2026-11-10，`<20261110151857.1864222-1-michalblk@google.com>`）*。作者注明 RESEND 相对 v3 无改动，仅 rebase 到 tip/sched/core，并补上 v3 阶段获得的 Andrea Reviewed-by 与 Tejun Acked-by。作者在 tip/sched/core + `x86_debug.config` 上复测：sched_ext selftests 全部通过；并发写所有 `cpu.*` 旋钮与 autogroup nice 时挂/摘 SCX 调度器无 lockdep 或其他告警。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：v1 阶段即认可「把锁上移到 core 层」的方向（正文引用其 v1 回复）。
- **Tejun Heo（sched_ext maintainer）**：v3 阶段给出 Acked-by，并曾请 Peter 收取 v3。
- **Andrea Righi（sched_ext 维护者）**：v3 阶段给出 Reviewed-by。
- 无 NAK、无未解决争议。系列已收敛到「等收取」状态。

## 合入评估

*likelihood=high*。方向获 Peter 认可、Tejun 与 Andrea 已背书，作者已做 lockdep/分裂复测且有 30/30 的复现→修复数据。*blocking_issues*：无实质阻塞，仅待维护者收取（作者目标是 tip/sched/core，同时干净可套 mainline）。*next_action*：Tejun/Peter 收取并合入 tip/sched/core。

## 效果评估

作者给出确定性的复现计数：在临时测试里让 BPF 调度器在 `ops.cgroup_set_{weight,idle,bandwidth}()` 中自旋 5ms、同时另一方写值，打补丁前 `cpu.weight`/`cpu.idle`/`cpu.max` 在 30/30 轮中均与 BPF 调度器所见值出现分歧；打补丁后 0/30。属正确性修复，无性能数据。

## 我可以参与的点

- **testing**：在带 SCX 调度器的场景并发压测 `cpu.weight`/`cpu.idle`/`cpu.max`/`cpu.weight.nice` 写，验证无分歧且无 lockdep 告警（可用作者自述的方法复现）。
- **review**：复核 `cpu_idle_write_s64()` 与 `cpu_weight_nice_write_s64()` 是否真的全部被同一把锁覆盖（这是作者列出的受影响写回，值得逐一对一遍）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110151857.1864222-1-michalblk@google.com/
- v3: https://lore.kernel.org/r/20260824074913.2468177-1-michalblk@google.com
- v2: https://lore.kernel.org/r/20260821140818.1559100-1-michalblk@google.com
- v1: https://lore.kernel.org/r/20260820160956.910663-1-michalblk@google.com
- Peter 对 v1 的认可: https://lore.kernel.org/r/20260821072653.GD4120091@noisy.programming.kicks-ass.net
