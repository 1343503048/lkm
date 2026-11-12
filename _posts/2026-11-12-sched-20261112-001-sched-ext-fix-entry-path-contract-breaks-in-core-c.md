---
id: sched-20261112-001
date: '2026-11-12'
subject: 'sched_ext: Fix entry-path contract breaks in core.c'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261112144935.583937-1-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20261112144935.583937-1-cui.tao@linux.dev/
authors:
- Tao Cui
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261112144935.583937-1-cui.tao@linux.dev>
  date: '2026-11-12'
  summary: fork 路径补 ENQUEUE_RQ_SELECTED；PI deboost 前 block retained donor
  review_outcome: Peter 对 patch 2 明确 NAK，指向 __setscheduler_class() 修根因
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - patch 2 的实现方式被 Peter NAK，需改为修 __setscheduler_class()
  next_action: 按 Peter 指向分析 __setscheduler_class() 的 EXT 缺陷并给替代修复；patch 1 可单独拆分
contribution_opportunities:
- kind: review
  description: 验证 __setscheduler_class() 对 EXT 的 bug 是否足以取代 patch 2 的 hook
- kind: new_patch
  description: 在类切换处统一处理 retained donor 的替代修复
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
- bpf
title: 'sched_ext: Fix entry-path contract breaks in core.c'
layout: article
---

## TL;DR

Tao Cui 发两补丁修复 sched_ext 在 core.c 里两处「进入路径契约」被破坏的问题：fork 路径 `wake_up_new_task()` 调了 `select_task_rq()` 却不带 `ENQUEUE_RQ_SELECTED`，导致 `SCX_EV_SELECT_CPU_FALLBACK` 永远不统计 fork 侧 fallback；`rt_mutex_setprio()` 是唯一不先 `sched_proxy_block_task()` 就进入 sched_ext 的路径，PI 提升后再 deboost 会把 ext 任务以「queued+blocked」的非法状态交回给 BPF 调度器。Peter Zijlstra 对 patch 2 明确 NAK（"sprinkling magic hooks... So no"），认为真正该修的是 `__setscheduler_class()`。

## 背景与问题

作者对照 `sched_ext/for-next`（5b740a72b55c）梳理 core.c 里所有进入 sched_ext 的路径，发现两条未满足 sched_ext 既有契约：

1. `select_task_rq()` 会置 `WF_RQ_SELECTED`，`ttwu_do_activate()` 把它映射成 `ENQUEUE_RQ_SELECTED`，让 `enqueue_task_scx()` 知道 `ops.select_cpu()` 已经跑过。但 `wake_up_new_task()`（fork 路径）同样调了 `select_task_rq()` 却在不带该标志的情况下 activate 新任务——于是 fork 路径上 `ops.enqueue()` 看不到 `SCX_ENQ_CPU_SELECTED`，`SCX_EV_SELECT_CPU_FALLBACK` 永远不计数 fork 侧 fallback，行为异常的 `select_cpu()` 在计数器里无迹可寻，依赖该标志的调度器还会对 `select_cpu()` 已放置好的任务重复跑一次 `select_cpu_dfl()`。
2. `rt_mutex_setprio()` 是唯一进入 sched_ext 却未先 `sched_proxy_block_task()` 的路径：一个被 rt waiter PI 提升的 ext 任务可在被提升期间阻塞在第二个内核 mutex 上，deboost 时被路由回 sched_ext 并携带「queued+blocked」状态——这正是 `scx_prepare_setscheduler()` 承诺绝不会发生的状态。

## 技术方案

两补丁（`kernel/sched/core.c` +17/-1、`kernel/sched/ext/ext.h` +2）：

1. `sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue`（`Fixes: 9b671793c7d9`）——在 `wake_up_new_task()` 里新增 `en_flags = ENQUEUE_NOCLOCK | ENQUEUE_INITIAL`，若 `select_task_rq()` 后 `wake_flags & WF_RQ_SELECTED` 则追加 `ENQUEUE_RQ_SELECTED`，再传给 `activate_task()`，与唤醒路径对齐。只有 sched_ext 消费该标志。
2. `sched_ext: Block a retained donor before PI deboost routes it back to sched_ext`（`Fixes: be8be8acb268`）——在 `rt_mutex_setprio()` 的 `sched_change` guard 之前，当类切换会把任务路由回 ext（`queue_flag & DEQUEUE_CLASS && next_class == &ext_sched_class`）时调 `scx_prepare_task_sched_change()`，补齐缺失的 `sched_proxy_block_task()`（附带的 `update_rq_clock()` 此处无害）。

## 版本演进与当前进展

*current_version: v1（2026-11-12，`<20261112144935.583937-1-cui.tao@linux.dev>`）*。当日发出，无版本演进；基于 `sched_ext/for-next`（5b740a72b55c）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra**：对 patch 2 明确 NAK——「I can't understand this. And I take a very dim view of sprinkling magic hooks like this. So no.」并进一步判定「据我目前的理解，`__setscheduler_class()` 对 EXT 是有 bug 的，该修的应该是那里」。即不认可在 `rt_mutex_setprio()` 里加 hook，而主张在 `__setscheduler_class()` 层面修根因。
- patch 1 未获单独表态（Peter 未回复 1/2）。分歧集中在 patch 2 的实现位置。

## 合入评估

*likelihood=low*。patch 2 被维护者 NAK 且被指向应修 `__setscheduler_class()`，当前形态不会合入；patch 1 独立且方向明确，但尚无维护者确认。*blocking_issues*：patch 2 的实现方式被 NAK，需改为修 `__setscheduler_class()`。*next_action*：作者按 Peter 的指向分析 `__setscheduler_class()` 的 EXT 缺陷并给出替代修复；patch 1 可单独拆分推进。

## 效果评估

作者在 qemu 上做了 A/B 验证：用探针强制 `select_cpu()` fallback，40k fork 里 baseline 为 0 次 fallback 事件（唤醒侧计数正常），打 patch 1 后 fork 与唤醒两条路径都 1:1 计数；driver-model 触发器在 baseline 上 40000 个 PI 周期交出约 39966 个 queued+blocked donor，patch 2 后为 0，PI 链流量不变。属正确性修复，无性能数据。

## 我可以参与的点

- **review**：验证 Peter 的判定——`__setscheduler_class()` 对 EXT 的 bug 具体在哪、是否足以取代 patch 2 的 hook 方案，这直接决定 patch 2 能否以正确形态合入。
- **new_patch**：若确认 `__setscheduler_class()` 缺陷，可协助提出/复核替代修复（在类切换处统一处理 retained donor），并在 `sched_ext/for-next` 上跑 qemu 的 PI + fork 回归。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261112144935.583937-1-cui.tao@linux.dev/
- Peter Zijlstra 对 patch 2 的 NAK: https://lore.kernel.org/all/20261112152118.GD1813469@noisy.programming.kicks-ass.net/
