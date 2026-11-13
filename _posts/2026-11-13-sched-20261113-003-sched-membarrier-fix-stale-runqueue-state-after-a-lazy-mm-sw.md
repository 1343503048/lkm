---
id: sched-20261113-003
subject: 'sched/membarrier: Fix stale runqueue state after a lazy mm switch'
date: 2026-11-13
subsystem: sched
type: bug
status: rfc
severity: critical
thread_root_msgid: <20261113131903.157186-2-mathieu.desnoyers@efficios.com>
lore_url: https://lore.kernel.org/all/20261113131903.157186-2-mathieu.desnoyers@efficios.com/
authors:
- Mathieu Desnoyers
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261113131903.157186-2-mathieu.desnoyers@efficios.com>
  date: 2026-11-13
  summary: membarrier_switch_mm() 改传 prev->mm 以强制刷新 lazy TLB / exit 场景的 rq->membarrier_state
  review_outcome: RFC 刚发出，暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待维护者对 RFC 系列（16 补丁）的评审
contribution_opportunities:
- kind: testing
  description: 复跑 lazy TLB 借用与 thread 退出两条触发链，验证 IPI 恢复送达
- kind: review
  description: 核查 prev->mm 与 prev->active_mm 在各路径上的语义差异
generated_at: '2026-11-14T01:30:00'
source_email_count: 2
related_articles: []
tags:
- membarrier
title: 'sched/membarrier: Fix stale runqueue state after a lazy mm switch'
layout: article
---

## TL;DR
Mathieu Desnoyers（membarrier 机制作者）发 RFC 系列（16 补丁）的修复之一：`MEMBARRIER_CMD_GLOBAL_EXPEDITED` 依赖 `rq->membarrier_state` 定位要发 IPI 的 CPU，但 `membarrier_switch_mm()` 用 `prev->active_mm` 与 `next->mm` 比较，导致 lazy TLB 借用与 thread 退出的两处场景下 runqueue 状态过期，注册进程在需要屏障时漏收 IPI——用户态看到的是内存排序失败，可能 free 掉注册进程仍在使用的内存（UAF）。修复改为传 `prev->mm`。已在 v7.4-rc2 上复现（1000 次命令对注册进程 0 次 IPI）。

## 背景与问题
`MEMBARRIER_CMD_GLOBAL_EXPEDITED` 会给每个运行注册进程的 CPU 发 IPI，它靠 `rq->membarrier_state`（mm 状态的 per-runqueue 副本）定位这些 CPU。commit `227a4aadc75b`（"sched/membarrier: Fix p->mm->membarrier_state racy load"）引入该副本；调度器在两次 mm 切换之间更新它；注册发生时发 IPI 更新仍在运行该 mm 的 runqueue。

`membarrier_switch_mm()` 比较 `prev->active_mm` 与 `next->mm`，所以当 prev 只是**借用** mm 时也跳过更新——两种情况会使副本过期：

- **Case 1**：进程注册期间，另一 CPU 上有个 lazy TLB 内核线程借用了它的 mm。CPU0 上的状态副本停在 0，注册方（在 CPU1）只更新自己 rq 的状态，CPU0 因 idle 无 IPI——之后 CPU0 恢复运行该进程时旧状态 0 未刷新，后续 GLOBAL_EXPEDITED 不给它发 IPI。
- **Case 2**：一个线程 exit（`exit_mm()` 清掉 runqueue 副本），随后 CPU 又跑同一进程的另一个线程（`prev->mm == next->mm`，跳过更新）——副本仍为 0。

`kthread_unuse_mm()` 与 `exit_mm()` 以相同方式清副本。两种情况下注册进程都"无承诺的内存屏障"运行，直到 CPU 从另一个 mm 切回它。

用户态表现为内存排序失败：注册进程省略快速路径屏障，调用方在需要屏障处发 GLOBAL_EXPEDITED（如共享内存上的 RCU 式同步）。没有 IPI 就会漏掉注册进程的最近 store，调用方可能 free 掉该进程仍在使用的内存。多线程注册进程中一个线程 exit 即可触发 case 2。两种 case 都在 v7.4-rc2 上复现：1000 次命令对注册进程 0 次 IPI。

## 技术方案
把 `membarrier_switch_mm()` 传递的参数由 `prev->active_mm` 改为 `prev->mm`——内核线程与已退出任务的 `prev->mm` 为 NULL，从而强制刷新副本；同一 mm 内的正常切回仍跳过（保持性能）。RFC 系列其余补丁（本次分析窗口仅收到其中 01/16 与 02/16 两封）另有四项修复与自测。

## 版本演进与当前进展
RFC 01/16 刚发出（作者称系列共 16 补丁，本窗口仅见 01、02 两封，cover 未收到）。尚未有对本文的回复。

## Maintainer 意见与讨论焦点
当日无针对本补丁的回复。作者是 membarrier 机制的设计者与 `227a4aadc75b` 的关联方，正文给出了精确的竞态时序图与 v7.4-rc2 复现数据，论证充分。

## 合入评估
属 RFC 发布，尚未有维护者表态；机制论证与复现完整，但需等待维护者确认后才会进入主线。作者已注明 Cc stable 的意图尚不明（正文未见 Fixes/Cc stable 行，全文以 RFC 形式发布）。

## 效果评估
正文给出复现数据：v7.4-rc2 上，1000 次命令对注册进程发送 0 次 IPI（预期为按需发送）。修复后未给出对比数字（RFC 阶段）。

## 我可以参与的点
- **testing**：复跑作者描述的 lazy TLB 借用与 thread 退出两条触发链，或验证补丁后 IPI 确实送达注册进程。
- **review**：核查 `prev->mm` 与 `prev->active_mm` 在 lazy TLB / `kthread_unuse_mm()` 路径上的全部语义差异，确认无回归。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261113131903.157186-2-mathieu.desnoyers@efficios.com/
