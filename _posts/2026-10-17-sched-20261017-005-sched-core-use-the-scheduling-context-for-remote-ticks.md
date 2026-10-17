---
id: sched-20261017-005
subject: 'sched/core: Use the scheduling context for remote ticks'
date: 2026-10-17
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>
lore_url: https://lore.kernel.org/all/20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>
  date: 2026-10-17
  summary: sched_tick_remote() 对 rq->donor 调用 task_tick()，移除 WARN_ON_ONCE(curr!=donor)，rq->curr
    仅做执行时间 sanity check
  review_outcome: 当日新发，暂无回帖
upstream_commit: null
fixes_commit: 7de9d4f94638
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  next_action: 等 proxy execution / nohz 相关维护者 review，补充更多负载验证
contribution_opportunities:
- kind: testing
  description: 在其他支持 proxy execution 的拓扑复现 WARNING 并验证修复后消失
- kind: review
  description: 审视 task_tick() 改到 donor 对 blocked donor 的语义等价性与 sanity check 上下文选择
generated_at: '2026-10-18T01:18:00'
source_email_count: 1
related_articles: []
tags:
- proxy_execution
- nohz
- tick
title: 'sched/core: Use the scheduling context for remote ticks'
layout: article
---

## TL;DR
Shubhang Kaushik（Ampere）发往 sched/core 的单补丁修复：full-nohz 远程 tick 路径 `sched_tick_remote()` 对 `rq->curr` 调用 `task_tick()`，但在 proxy execution 下 `rq->curr` 是 mutex-owner 执行上下文、`rq->donor` 才是提供调度上下文的阻塞任务——作者用 Ampere Altra + `CONFIG_SCHED_PROXY_EXEC=y` + `nohz_full=78` + RT boosting 触发了 `WARN_ON_ONCE(rq->curr != rq->donor)`。补丁改为对 `rq->donor` 调用 `task_tick()`（与 `sched_tick()`/`hrtick()` 对齐），仅保留 `rq->curr` 做执行时间 sanity check。当日新发，暂无回帖。

## 背景与问题
`sched_tick_remote()`（full dynticks 的远程 tick worker）对 `rq->curr` 调用 `task_tick()`。在 proxy execution 下，`rq->curr` 是 mutex-owner 执行上下文，而 `rq->donor` 才是被阻塞、提供调度上下文的任务。一个 mutex 阻塞的任务仍为 proxy execution 排队；若它是 SCHED_FIFO、或唯一的 SCHED_RR 任务，`sched_can_stop_tick()` 会允许 full-nohz tick 停止。之后 `find_proxy_task()` 可以把它的 mutex owner 选为 `rq->curr`，同时保留阻塞任务为 `rq->donor`。此时远程 tick 落在 `rq->curr`（owner）上做调度记账，与真正该记账的 `rq->donor` 不一致，且原代码里 `WARN_ON_ONCE(rq->curr != rq->donor)` 的假设（「remote tick 时只有一个任务在跑、无 proxy」）已被 proxy execution 打破。

## 技术方案
单补丁（`kernel/sched/core.c`，+6/−7）：`sched_tick_remote()` 中把 `curr->sched_class->task_tick(rq, curr, 0)` 改为 `donor->sched_class->task_tick(rq, donor, 0)`（新增 `struct task_struct *donor = rq->donor;`），并移除 `WARN_ON_ONCE(rq->curr != rq->donor)`。`rq->curr` 保留用于执行时间 sanity check（`rq_clock_task(rq) - curr->se.exec_start` 超 30s 的 `WARN_ON_ONCE`）。这是对 `sched_tick()`/`hrtick()` 已对 `rq->donor` 记账的既有约定的补齐。带 `Fixes: 7de9d4f94638`（"sched: Start blocked_on chain processing in find_proxy_task()"）。

## 版本演进与当前进展
v1 首版（`<20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org>`，base-commit `70dd4ee72eb2`），当日新发，暂无 review 意见。

## Maintainer 意见与讨论焦点
当日无回帖。潜在评审点（无人提出）：`task_tick()` 改挂到 `donor` 后，donor 为 blocked 任务时其 `task_tick` 语义是否完全等价于 `rq->curr` 版本；以及远程 tick 下 donor 与 curr 的执行时间 sanity check 应基于哪个上下文。

## 合入评估
*likelihood=unknown*。改动小而语义清晰、与 `sched_tick()`/`hrtick()` 对齐，但当日无任何 review。*blocking_issues*：无 review。*next_action*：等 proxy execution（或全 nohz）相关维护者 review；可补充更多负载下的验证数据。

## 效果评估
作者测试：Ampere Altra，`CONFIG_SCHED_PROXY_EXEC=y`、`CONFIG_NO_HZ_FULL=y`，`sched_proxy_exec=1 nohz_full=78`。未打补丁基线（`70dd4ee72eb2`，7.3.0-rc7）下，mutex locktorture 四 writer 固定到 CPU 78 并触发 RT boosting，命中 `WARNING: kernel/sched/core.c:5895 at sched_tick_remote`（即 `WARN_ON_ONCE(rq->curr != rq->donor)`），证明 full-nohz 远程 tick 确实能在执行任务与调度上下文不一致时运行。打补丁后同一 10 分钟负载完成，无 scheduler WARNING、无 locktorture 失败。无量化性能数据。

## 我可以参与的点
- *testing*：在其他支持 proxy execution 的拓扑（如更多 CPU/不同锁竞争模式）复现警告并验证修复后消失。
- *review*：审视 `task_tick()` 从 `curr` 改到 `donor` 对 blocked donor 的语义等价性，以及执行时间 sanity check 上下文的选择。

## 参考链接
- patch：https://lore.kernel.org/all/20261016-remote-tick-proxy-v1-1-272757a50a07@gentwo.org/
