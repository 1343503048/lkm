# sched: Lift cgroup update locking to core to prevent CFS/SCX divergence

## TL;DR

Michal Blaszczyk 的 CFS/SCX 状态分歧修复**今日合入 tip/sched/urgent**（commit `342fe98c3431`）：并发写 cgroup 控制文件（`cpu.shares`/`cpu.weight`/`cpu.max`/`cpu.idle`/`cpu.weight.nice`）时，CFS 的 `shares_mutex` 在调用 `scx_group_set_weight()` 前就被释放，导致 CFS、SCX 内部记账与 BPF 调度器三者看到互不一致的参数。修复把 CFS 锁上移到 `kernel/sched/core.c` 的核心写回处理器，使 CFS 与 SCX 回调同一把锁下原子执行（Fixes: 819513666966）。此前已有 Tejun Acked-by、Andrea Righi Reviewed-by。

## 背景与问题

（承接 sched-20261110-001）`cpu_shares_write_u64()` 里 CFS 更新由 fair.c 内部的 `shares_mutex` 串行化，但该锁在 `scx_group_set_weight()` 前释放，后者只拿读信号量 `scx_cgroup_ops_rwsem`；并发写可交错，使 CFS 记录、`tg->scx.weight`、BPF 调度器参数两两不同。同类竞态存在于 `tg_set_bandwidth()`、`cpu_idle_write_s64()`、`cpu_weight_write_u64()`、`cpu_weight_nice_write_s64()`。

## 技术方案

（承接）把 CFS 锁上移到 core 层：`kernel/sched/core.c` 新增全局 mutex 替换 fair.c 内部锁，在核心写回处理器里用 guard 包裹 CFS 与 SCX 更新，使两者原子执行（core.c +35/-12、fair.c +25/-12、sched.h +7）。

## 版本演进与当前进展

已合入 tip/sched/urgent（`342fe98c3431`，AuthorDate 2026-11-10，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：Acked-by（承接）。
- **Andrea Righi（sched_ext 维护者）**：Reviewed-by（承接）。
- **Peter Zijlstra**：Committer 合入（此前 v1 即认可「锁上移 core」方向）。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/urgent（`342fe98c3431`）。*blocking_issues*：无。*next_action*：随 sched/urgent 进入 7.4-rc 修复。

## 效果评估

作者此前给出确定复现：BPF 调度器在 `ops.cgroup_set_{weight,idle,bandwidth}` 自旋 5ms 时，打补丁前 `cpu.weight`/`cpu.idle`/`cpu.max` 30/30 轮分歧；打补丁后 0/30。属正确性修复。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/342fe98c34311969950fa58a840fd0b95a16c9dd
- lore thread: https://lore.kernel.org/all/20261110151857.1864222-1-michalblk@google.com/

---
id: sched-20261118-024
date: '2026-11-18'
subject: "sched: Lift cgroup update locking to core to prevent CFS/SCX divergence"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261110151857.1864222-1-michalblk@google.com>"
lore_url: "https://lore.kernel.org/all/20261110151857.1864222-1-michalblk@google.com/"
authors: [Michal Blaszczyk]
maintainers_involved: [Tejun Heo, Andrea Righi, Peter Zijlstra]
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261110151857.1864222-1-michalblk@google.com>"
    date: '2026-11-10'
    summary: "CFS 锁上移 core 层，CFS/SCX 回调原子执行"
    review_outcome: "Tejun Ack、Andrea RB，合入 sched/urgent"
upstream_commit: "342fe98c34311969950fa58a840fd0b95a16c9dd"
fixes_commit: "819513666966"
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/urgent 进入 7.4-rc 修复"
contribution_opportunities: []
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261110-001]
tags: [cgroup, sched_ext, cfs]
---
