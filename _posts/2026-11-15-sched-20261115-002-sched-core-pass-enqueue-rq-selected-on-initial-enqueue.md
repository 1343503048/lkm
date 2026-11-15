---
id: sched-20261115-002
date: '2026-11-15'
subject: 'sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261112144935.583937-2-cui.tao@linux.dev>
lore_url: https://lore.kernel.org/all/20261112144935.583937-2-cui.tao@linux.dev/
authors:
- Tao Cui
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261112144935.583937-2-cui.tao@linux.dev>
  date: '2026-11-12'
  summary: wake_up_new_task() 里给初始入队补 ENQUEUE_RQ_SELECTED，与唤醒路径对齐
  review_outcome: Tejun Acked，待 Peter 确认路由
upstream_commit: null
fixes_commit: 9b671793c7d9
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 路由未定：走 sched/core 还是 sched_ext，需 Peter 确认
  next_action: 等 Peter 回应路由；或由 Tejun 经 sched_ext 收取
contribution_opportunities:
- kind: review
  description: 核对 ENQUEUE_RQ_SELECTED 在初始入队路径的语义与唤醒路径一致性
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261112-001
tags:
- sched_ext
- cfs
title: 'sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-001-sched-ext-fix-entry-path-contract-breaks-in-core-c.html">sched-20261112-001</a>：Tao Cui 两补丁修复 sched_ext 在 core.c 里的进入路径契约；其中 patch 1 即本系列 `sched/core: Pass ENQUEUE_RQ_SELECTED on initial enqueue`——在 fork 路径 `wake_up_new_task()` 里给初始入队补上 `ENQUEUE_RQ_SELECTED`，与唤醒路径对齐（只有 sched_ext 消费该标志）。当时 Peter 只对 patch 2 表态 NAK，patch 1 未获单独确认。
- <a class="article-ref" href="/lkm/2026/11/15/sched-20261115-002-sched-core-pass-enqueue-rq-selected-on-initial-enqueue.html">sched-20261115-002</a>（今天）：Tejun Heo 对 patch 1 给出 Acked-by，并询问 Peter 该补丁走 sched/core 还是 sched_ext 路由（因该标志仅 sched_ext 消费，Tejun 愿意经 sched_ext 收取）。

## 背景与问题

sched_ext 在 core.c 里有「进入路径契约」约定：`ops.enqueue()` 需要知道 `ops.select_cpu()` 是否已跑过。唤醒路径 `ttwu_do_activate()` 会把 `select_task_rq()` 置的 `WF_RQ_SELECTED` 映射成 `ENQUEUE_RQ_SELECTED`；但 fork 路径 `wake_up_new_task()` 同样调了 `select_task_rq()` 却不带该标志激活新任务——于是 fork 侧 `ops.enqueue()` 看不到 `SCX_ENQ_CPU_SELECTED`，`SCX_EV_SELECT_CPU_FALLBACK` 永远不计数 fork 侧 fallback，依赖该标志的调度器还会对 `select_cpu()` 已放置好的任务重复跑一次 `select_cpu_dfl()`。

## 技术方案

在 `wake_up_new_task()` 里新增 `en_flags = ENQUEUE_NOCLOCK | ENQUEUE_INITIAL`，若 `select_task_rq()` 后 `wake_flags & WF_RQ_SELECTED` 则追加 `ENQUEUE_RQ_SELECTED`，再传给 `activate_task()`，与唤醒路径对齐（`Fixes: 9b671793c7d9`）。改动限定 core.c，只有 sched_ext 消费该标志，对其它调度类无影响。

## 版本演进与当前进展

*current_version: v1（2026-11-12，`<20261112144935.583937-2-cui.tao@linux.dev>`）*。当日无新版本，进展为 Tejun 的 Ack 与路由询问。

## Maintainer 意见与讨论焦点

- **Tejun Heo**：Acked-by，并问 Peter 想怎么路由——由于该标志只有 sched_ext 消费，他愿意经 sched_ext 树收取。
- **Peter Zijlstra**：当日未回帖；此前对同系列的 patch 2 已明确 NAK，但与本 patch 1 无关（此前 patch 2 的争议点在 `rt_mutex_setprio()` 加 hook 的位置）。

## 合入评估

*likelihood=high*。patch 1 独立、方向明确且已获 Tejun Ack。*blocking_issues*：路由未定（sched/core vs sched_ext），需 Peter 确认。*next_action*：等 Peter 回应路由；若 Peter 无异议，可由 Tejun 经 sched_ext 收取。

## 效果评估

属正确性修复，无性能数据。此前系列作者在 qemu 上 A/B 验证：40k fork 中打 patch 1 后 fork 与唤醒两条路径均 1:1 计数 fallback 事件（patch 前 fork 侧为 0）。

## 我可以参与的点

- **review**：核对 `ENQUEUE_RQ_SELECTED` 在初始入队路径的语义是否与唤醒路径完全一致，以及是否还有 sched_ext 之外遗留的消费方或边界路径（如 kernel_clone 的其它调用点）。

## 参考链接

- lore thread (patch 1/2): https://lore.kernel.org/all/20261112144935.583937-2-cui.tao@linux.dev/
- Tejun 的 Ack: https://lore.kernel.org/all/598bee2c48b23aee00c404d1183b581a@kernel.org/
- 前序系列总览 (cover letter): https://lore.kernel.org/all/20261112144935.583937-1-cui.tao@linux.dev/
