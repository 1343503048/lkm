---
id: sched-20260809-006
date: 2026-08-09
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20260809.owner_on_cpu.uaf@yangzi>
lore_url: 未获取到
authors:
- Yang Zi
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
- Waiman Long
- Boqun Feng
current_version: report
patch_series:
- version: report
  msgid: <20260809.owner_on_cpu.uaf@yangzi>
  date: 2026-08-09
  summary: 同一 fuzzer 作者通过 3 个不同驱动路径（iavf、dw_edma_pcie、bna）复现同一 root cause：mutex 乐观自旋读取
    owner 任务的 on_cpu 字段时，owner 任务结构体已被释放，触发 KASAN use-after-free。
  review_outcome: 3 封均为 KASAN 报告，属同一已知 mutex 乐观自旋 owner 生命周期问题，暂无维护者修复 patch。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 需要确认根因是 mutex 乐观自旋对 owner 任务 on_cpu 的访问缺少引用保护，还是调用方驱动问题
  next_action: locking/sched 维护者定位 owner_on_cpu 访问的引用语义，确认是否需要持 rcu/引用计数保护。
contribution_opportunities:
- kind: review
  description: 分析 mutex_can_spin_on_owner/owner_on_cpu 在 owner 释放后的生命周期保护是否充分。
- kind: testing
  description: 在开启 KASAN + 对应驱动(网卡/iavf、dma/dw_edma)的场景复现并验证修复。
generated_at: '2026-08-10T00:15:00'
source_email_count: 3
related_articles: []
tags:
- sched/core
- locking
- crash
- syzbot
title: 'KASAN: slab-use-after-free in owner_on_cpu via iava_remove (mutex optimistic
  spin) [iavf] [syzkaller]'
layout: article
---

## TL;DR
2026-08-09 收到 3 封 KASAN use-after-free 报告（通过 iavf、dw_edma_pcie、bna 三种驱动触发），根因相同：mutex 乐观自旋读取 owner 任务的 `on_cpu` 字段时任务结构体已释放。属 high 严重度崩溃类 bug，尚无修复 patch。

## 背景与问题
`sched.h` 中的 `owner_on_cpu()` 被 mutex 乐观自旋路径用于判断锁的 owner 当前是否正在 CPU 上运行。3 份报告均显示：在 owner 任务已被释放（退出）后，自旋路径仍读取其 `task_struct->on_cpu`，触发 KASAN slab-use-after-free。触发路径虽经不同驱动（网卡 iavf、PCIe DMA dw_edma、网卡 bna），但核心都是同一处对 owner 任务生命周期的访问缺乏充分保护。

## 技术方案
报告为 bug 复现，未附修复 patch。修复方向预期是：在乐观自旋读 `on_cpu` 时保证 owner 任务结构体的引用/rcu 保护，或在 owner 释放路径上正确同步自旋退出。具体方案需 locking/sched 维护者定。

## 版本演进与当前进展
当前为 3 份独立 KASAN 报告（同一 root cause），均于 8/9 发出，暂无 review/修复。

## Maintainer 意见与讨论焦点
暂无维护者明确意见。关键是区分「这是 mutex 乐观自旋自身的引用语义缺陷」还是「驱动误用导致 owner 提前释放」。从 3 条不同驱动触发同一处看，更倾向前者。

## 合入评估
合入可能性 unknown。需先定位根因。若确认是 mutex 乐观自旋生命周期问题，预计会有较高优先级修复。

## 效果评估
暂无修复效果数据；报告本身给出 KASAN 调用栈（如 `task_on_cpu`/`owner_on_cpu` ← `mutex_optimistic_spin` 路径），复现稳定。

## 我可以参与的点
- 分析 `mutex_can_spin_on_owner` / `owner_on_cpu` 在 owner 释放后的保护是否充分，提出 rcu/引用计数方案；
- 在 KASAN 内核 + iavf/dw_edma 场景复现并验证候选修复。

## 参考链接
- lore thread: 未获取到
- KASAN 报告: 未获取到完整链接
