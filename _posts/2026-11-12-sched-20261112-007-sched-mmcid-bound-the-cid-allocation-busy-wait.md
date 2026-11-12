---
id: sched-20261112-007
date: '2026-11-12'
subject: 'sched/mmcid: Bound the CID allocation busy wait'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn>
lore_url: https://lore.kernel.org/all/bd4c03e6-7ea6-4a21-9a3e-74ea9d36fe17@efficios.com/
authors:
- Jiakai Xu
maintainers_involved:
- Peter Zijlstra
- Thomas Gleixner
- Mathieu Desnoyers
current_version: v1
patch_series:
- version: v1
  msgid: <20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn>
  date: '2026-09-18'
  summary: 为 mm_get_cid 无界自旋加 32 次重试上限，耗尽返回 MM_CID_UNSET
  review_outcome: Peter 强烈质疑；Mathieu 今日补上复现器确认锁死
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 的语义质疑未回应
  - 修复方案与复现根因的对齐关系待明确
  next_action: 结合 Mathieu 复现器回应 Peter 质疑，明确修 mm_cid 记账还是加界
contribution_opportunities:
- kind: discussion
  description: 分析失败 execve 丢 CID 与 mm_get_cid 无界自旋哪处是应修根因
- kind: testing
  description: 复跑 Mathieu 的失败 execve + 迁移触发链验证候选修复
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20260918-003
- sched-20261021-020
tags:
- cgroup
- cfs
title: 'sched/mmcid: Bound the CID allocation busy wait'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-003-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20260918-003</a>：Jiakai Xu 提交修复——为 `mm_get_cid()` 的无界自旋加 32 次重试上限；Peter Zijlstra 强烈质疑（"horribly wrong"），认为未解释切换为何不发生、如何不破坏用户态。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-020-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20261021-020</a>：Thomas Gleixner 追问复现器，作者 Jiakai 承认「没有 reproducer」。
- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-007-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20261112-007</a>（今天）：**Mathieu Desnoyers（mm_cid 机制设计者）自己构造出复现器并确认了锁死**——他描述 Thomas 担忧的 stale 状态再加两个条件（execve() 失败 + execve 期间任务被迁到另一 CPU）即可触发：单线程 `mm_get_cid()` 循环在 `sched_mm_cid_fork()` 里，导致 `pthread_create()` 卡死。这补上了此前缺失的复现依据，Peter 质疑的「切换为何不发生」有了具体场景。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-003-sched-mmcid-bound-the-cid-allocation-busy-wait.html">sched-20260918-003</a> / 20261021-020）`mm_get_cid()` 无可用 CID 时永久自旋，调用者持 rq 锁/`mm::mm_cid::lock` 且关中断，CID bitmap 耗尽时可升级为 RCU stall / 整机 lockup。核心未解问题（Peter 提出）是「为何切换不发生」与「如何不破坏用户态」，而此前作者无法提供复现器。今日 Mathieu 给出确定性触发链：失败的 `execve()` 会 rejoin 它离开的 mm——初始分配成功（如 Thomas 所指），但 CID 被置起却无 owner，mm 丢失一个 CID；随后单线程读到 `mm_cid 1`（应读 0）而非 0。在双 CPU guest 上两个 bit 都被置起后，下一次 `pthread_create()` 在 `mm_get_cid()`/`sched_mm_cid_fork()` 里循环，锁死。复现于 tip sched/urgent（006991aa8997），双/三 CPU guest。

## 技术方案

（承接 v1）`MM_CID_GET_RETRIES 32` 上限 + 耗尽返回 `MM_CID_UNSET` + 各调用点 schedule-in 重试。今日无新代码：Mathieu 提供了复现器与 stale 状态到锁死的完整因果图（失败 execve 丢失一个 CID → 单线程读到 mm_cid 1 → 双 CPU 上两 bit 全置起 → fork 时 mm_get_cid 自旋）。该复现路径也区分了「本锁死」与 Jiakai 此前报告的 splat（Mathieu 明确说这不是 Jiakai 报的那个 splat）。

## 版本演进与当前进展

*current_version: v1*（无新版本）。今日进展是复现器被补齐（由 mm_cid 机制作者 Mathieu 提供），从「作者无法复现」推进到「有确定性复现」。

## Maintainer 意见与讨论焦点

- **Mathieu Desnoyers**：作为 mm_cid 设计者主动构造并确认锁死，回应对 stale 状态的既有担忧（Thomas Gleixner 此前提出），并把失败 execve + 迁移的因果链写进 changelog 图。
- **Peter Zijlstra / Thomas Gleixner**：当日无新回帖，但 Peter 此前 "horribly wrong" 的语义质疑（切换为何不发生、是否破坏用户态）现在有了可对齐的具体场景。
- 无 NAK；核心问题是修复方案（32 次重试上限）的正当性仍需维护者认可。

## 合入评估

*likelihood=low*。复现器被补齐是重要进展，但 Peter 对修复方案的强烈质疑仍未化解，且 Jiakai 的 32 次重试上限方案与 Mathieu 描述的锁死根因（stale 状态 / 失败 execve 丢 CID）是否同源、应修哪一层，尚待维护者定调。*blocking_issues*：Peter 的语义质疑未回应；修复方案与复现根因的对齐关系待明确。*next_action*：结合 Mathieu 的复现器回应 Peter 的语义质疑，明确「应修 mm_cid 记账还是给 mm_get_cid 加界」的取舍。

## 效果评估

无量化数据；进展为复现器被补齐（Mathieu 在双/三 CPU guest 上确定性锁死），使「CID 耗尽→永久自旋」不再是无实证的场景。

## 我可以参与的点

- **discussion**：结合 Mathieu 的复现器分析「失败 execve 丢 CID」与「mm_get_cid 无界自旋」两处哪处才是应修的根因——这直接决定 Peter 的质疑能否被回应、修复该落在 mm_cid 记账还是 busy-wait 限界。
- **testing**：在带 mm_cid 的压力场景复跑 Mathieu 的失败 execve + 迁移触发链，验证候选修复是否消除 `pthread_create()` 锁死。

## 参考链接

- Mathieu 的复现器: https://lore.kernel.org/all/bd4c03e6-7ea6-4a21-9a3e-74ea9d36fe17@efficios.com/
- 原始补丁: https://lore.kernel.org/all/20260918013454.1850369-1-xujiakai24@mails.ucas.ac.cn/
