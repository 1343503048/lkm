---
id: sched-20261016-017
date: 2026-10-16
subject: 'sched: add need-resched timed wait interface'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261016070837.440748-1-ankur.a.arora@oracle.com>
lore_url: https://lore.kernel.org/all/20261016070837.440748-1-ankur.a.arora@oracle.com/
authors:
- Ankur Arora
maintainers_involved:
- Rafael J. Wysocki
current_version: v16
patch_series:
- version: v16
  msgid: <20261016070837.440748-12-ankur.a.arora@oracle.com>
  date: 2026-10-16
  summary: 11/16 新增 tif_need_resched_relaxed_wait()；12/16 poll_idle() 改用该接口
  review_outcome: 12/16 获 Rafael Acked-by 与 Haris Tested-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - sched 侧维护者意见与其余补丁本批未见
  next_action: 观察 sched 侧维护者对接口的反馈与系列整体走向
contribution_opportunities:
- kind: review
  description: 核对 tif_bitset_relaxed_wait() 的 local_clock 域与不可抢占前提在所有调用点成立
generated_at: '2026-10-17T01:30:00'
source_email_count: 2
related_articles: []
tags:
- idle
- nohz
title: 'sched: add need-resched timed wait interface'
layout: article
---

## TL;DR
Ankur Arora 的 v16 16 补丁系列（need-resched timed wait）继续推进：本次缓存到其中两封——11/16 在 `linux/sched/idle.h` 新增 `tif_bitset_relaxed_wait()` / `tif_need_resched_relaxed_wait()` 接口（基于 `smp_cond_load_relaxed_timeout()`），12/16 让 `cpuidle/poll_state` 的 `poll_idle()` 改用该接口。12/16 已获 Rafael Wysocki 的 `Acked-by` 与 Haris Okanovic 的 `Tested-by`。

## 背景与问题
`poll_idle()` 的内层循环轮询 thread_info flags、等待 TIF_NEED_RESCHED 被置位或 poll 时限到期；为省指令对时间检查做了 rate-limit，每轮 `cpu_relax()` 给流水线省电提示。该系列希望把这套「等待 need-resched 直到超时」的模式抽象成通用接口，供 poll_idle 及其它需要 relaxed 等待的场景复用。

## 技术方案
- **11/16（`include/linux/sched/idle.h`，+29）**：新增 `tif_bitset_relaxed_wait(int tif, u64 timeout_ns)`（用 `smp_cond_load_relaxed_timeout()` 实现「bit 置位或超时」等待，调用方需保证当前上下文不可抢占/迁移，从而安全待在 local_clock 域），并封装出 `tif_need_resched_relaxed_wait(u64 timeout_ns)`。放在 `sched/idle.h` 而非 `thread_info.h` 以规避递归 include。
- **12/16（`drivers/cpuidle/poll_state.c`，+1/−20）**：`poll_idle()` 改用 `tif_need_resched_relaxed_wait()`，删掉手写的 rate-limited 轮询循环；为省电仍以 `CONFIG_ARCH_HAS_CPU_RELAX` 作为 `cpuidle/poll_state.c` 的构建门槛（该配置指示平台有优化的 `smp_cond_load_relaxed_timeout()`）。

## 版本演进与当前进展
v16（<20261016070837.440748-1-ankur.a.arora@oracle.com>）为长线系列（从早期版本一路迭代）。本次仅缓存到 11/16、12/16 两封，其余 14 封未进缓存。12/16 带 `Acked-by: Rafael J. Wysocki`、`Tested-by: Haris Okanovic`、`Suggested-by: Rafael J. Wysocki`。

## Maintainer 意见与讨论焦点
Rafael J. Wysocki（cpuidle/pm 维护者）对 12/16 给 Acked-by 并 Suggested-by，方向获 pm 侧认可。sched 侧（Ingo/Peter）意见本批未见。

## 合入评估
*likelihood=unknown*。长线系列（v16）、pm 侧已 Ack，但 sched 侧维护者意见与其余补丁内容本批未见，难以判断整体。*blocking_issues*：sched 侧维护者尚未在本批表态；仅 2/16 可见。*next_action*：观察 sched 侧维护者对接口的反馈与系列整体走向。

## 效果评估
无量化数据（接口抽象 + 省指令 refactor，12/16 有 Haris Okanovic 的 Tested-by，但未附数字）。

## 我可以参与的点
- *review*：核对 `tif_bitset_relaxed_wait()` 的 local_clock 域与不可抢占/迁移前提是否在所有调用点成立。

## 参考链接
- 系列 cover（thread）：https://lore.kernel.org/all/20261016070837.440748-1-ankur.a.arora@oracle.com/
- 11/16：https://lore.kernel.org/all/20261016070837.440748-12-ankur.a.arora@oracle.com/
- 12/16：https://lore.kernel.org/all/20261016070837.440748-13-ankur.a.arora@oracle.com/
