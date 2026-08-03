---
id: sched-20260731-003
date: 2026-07-31
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260731081413.5505-1-wangfengyu@hygon.cn>"
lore_url: "https://lore.kernel.org/lkml/20260731081413.5505-1-wangfengyu@hygon.cn"
authors: [Fengyu Wang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260731081413.5505-1-wangfengyu@hygon.cn>"
    date: 2026-07-31
    summary: "sched_init_numa() 中 topology 数组分配失败时，撤销并释放已发布的 numa_masks，修复内存泄漏"
    review_outcome: "v1 刚发出，暂无 review 意见"
upstream_commit: null
fixes_commit: "cb83b629bae0"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待 review"
contribution_opportunities: []
generated_at: "2026-07-31T16:30:00"
source_email_count: 1
related_articles: []
tags: [topology, numa_balancing]
---

## TL;DR

Fengyu Wang (Hygon) 修复 sched_init_numa() 中 topology 数组分配失败时的内存泄漏：masks 已发布但无法释放。补丁增加失败路径中的 masks 清理逻辑。带有 Fixes: 标签指向原始 commit cb83b629bae0。v1 刚发出，暂无 review 意见，合入可能性高。

## 背景与问题

`sched_init_numa()` 在分配 topology 数组之前就已经发布了 `sched_domains_numa_masks`（通过 RCU 发布）。当后续的 topology 数组 `kzalloc()` 失败时，函数直接 return，导致：

- masks 已被 RCU 发布，但 `sched_domains_numa_levels` 仍为零
- 没有代码能 dereference 这些 masks，但也没有代码能 free 它们
- 为这些 masks 构建的 topology 永远不会被安装

这是一个经典的"发布后分配失败"内存泄漏问题。

## 技术方案

在 `kzalloc()` 失败路径中增加清理逻辑：

1. `rcu_assign_pointer(sched_domains_numa_masks, NULL)` — 撤销 RCU 发布
2. `synchronize_rcu()` — 等待所有 reader 完成
3. 遍历释放所有 `masks[i][j]` 和 `masks[i]` 以及 `masks` 本身

修改 11 行代码（+10/-1），在 `kernel/sched/topology.c` 中。

作者通过硬编码 `tl = NULL` 强制触发失败路径进行了测试，确认 masks 被正确释放且机器正常启动。

## 版本演进与当前进展

- **v1**（2026-07-31）：刚发出，暂无 review 意见

## Maintainer 意见与讨论焦点

暂无。

## 合入评估

- **likelihood: high** — 修复逻辑清晰，带有 Fixes: 标签，作者已测试验证
- **blocking_issues**: 无
- **next_action**: 等待 maintainer review

## 效果评估

暂无效果数据。此修复解决内存泄漏问题，仅在 topology 数组分配失败（通常是内存极度紧张）时触发。

## 我可以参与的点

当前阶段暂无明显参与空间，修复简单明确。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260731081413.5505-1-wangfengyu@hygon.cn
- Fixes: cb83b629bae0 ("sched/numa: Rewrite the CONFIG_NUMA sched domain support")
