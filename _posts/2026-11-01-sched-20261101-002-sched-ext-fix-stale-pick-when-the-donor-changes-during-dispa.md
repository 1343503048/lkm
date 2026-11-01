---
id: sched-20261101-002
subject: 'sched_ext: Fix stale pick when the donor changes during dispatch'
date: 2026-11-01
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261031162803.541236-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261031162803.541236-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved: []
current_version: v4
patch_series:
- version: v1
  msgid: null
  date: 2026-10-30
  summary: 初版，修复 proxy execution 下 dispatch 中 donor 被改导致的 stale pick
  review_outcome: 本次窗口外，早期版本不在分析窗口内
- version: v2
  msgid: null
  date: 2026-10-30
  summary: 补覆盖 dispatch 内部 drop rq lock 的情况
  review_outcome: 回应 sashiko 意见
- version: v3
  msgid: null
  date: 2026-10-31
  summary: 不在 ops.dispatch() 之后保留 stale @prev
  review_outcome: 回应 sashiko 意见
- version: v4
  msgid: <20261031162803.541236-1-tj@kernel.org>
  date: 2026-10-31
  summary: 补覆盖 core scheduling 下 sibling 换掉 @prev 的情况并改标题
  review_outcome: Andrea Righi Reviewed-by；rq->dl_server 问题另起 follow-up
upstream_commit: null
fixes_commit: 7b0888b7cc19
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 收尾合入 sched_ext/for-7.4-fixes；Andrea 提出的 rq->dl_server 问题另行处理
contribution_opportunities:
- kind: review
  description: 核对 scx_dsp_prev_stale() 在各 drop lock 点的覆盖是否完整
- kind: testing
  description: 在真实 sched_ext 调度器上验证 core scheduling + proxy execution 组合稳定性
generated_at: '2026-11-02T09:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
- proxy_execution
- core_sched
title: 'sched_ext: Fix stale pick when the donor changes during dispatch'
layout: article
---

## TL;DR

修复 sched_ext dispatch 过程中 rq->donor 被其他 CPU 改掉后仍沿用旧 `@prev` 导致的 stale pick（可能让本 CPU 运行一个已排队到别的 rq 的任务）。v4 已获 Andrea Righi Reviewed-by，属于 for-7.4-fixes，Cc stable v6.12+，合入可能性高。

## 背景与问题

dispatch 以 `rq->donor` 作为 `@prev` 且可能 drop rq lock。开启 proxy execution 后 `@prev` 未必是正在运行的任务，另一 CPU 可在 dispatch drop lock 期间通过 `proxy_needs_return()`（wakeup）或 `sched_proxy_block_task()`（调度类/调度器切换）把 donor 重置为 `rq->curr`。典型 wakeup 场景：dispatch_one() drop lock 移动任务时，另一 CPU wake 被 proxy 迁到本 CPU 的 donor，`proxy_needs_return()` 将其 dequeue 并重置 donor，随后 wakeup 把它 enqueue 到别的 CPU；dispatch_one() 看到 `@prev` 仍 queued 返回 SCX_DSP_PREV，本 CPU 运行了一个排队在其他 rq 的任务。core scheduling 下核心 pick 会以各 sibling 的 donor 为 `@prev` 跑 dispatch，sibling 也可能在 drop lock 时换掉 `@prev`。`rq_modified_above()` 仅在 rq->curr 高于 ext 的调度类时才能捕获，dl_server pick 则完全跳过该检查。

## 技术方案

当 `@prev` 不再是 donor 时重启 pick。`dispatch_one()` 在每个可能 drop lock 的步骤后调用 `scx_dsp_prev_stale()` 检测；`scx_dispatch_sched()` 在每次 `ops.dispatch()` 调用前决定是否把 `@prev` 交给 BPF 调度器，同样覆盖跨 drop 的调度类/调度器切换。新增 `scx_dsp_prev_stale()`：`(sched_proxy_exec() || sched_core_enabled(rq)) && unlikely(prev != rq->donor)`。仅 proxy execution 时 donor 在 pick 中只会变回 rq->curr，重试后不会再次 stale；core scheduling 下重试走 core pick（其本身已对 lock drop 重试）。作者提到 `7a3a6bfbd62a`（"sched: Rework prev_balance() to avoid stale prev references"）已用读 rq->donor 而非取 @prev 的方式关闭 prev_balance() 的同类窗口，但这里不适用（dispatch 从未评估过新 donor，其甚至可能不是 sched_ext 任务）。`Fixes: 7b0888b7cc19`（sched_ext core-sched 支持）、`Fixes: c6fe97c34a1a`（sched 允许 proxy exec 与 sched_ext 共存），Cc stable v6.12+。

## 版本演进与当前进展

- **v1**：初版（本次窗口外）。
- **v2**：补覆盖 dispatch 内部 drop rq lock 的情况（回应 sashiko）。
- **v3**：不在 `ops.dispatch()` 之后保留 stale `@prev`（回应 sashiko）。
- **v4**（当前）：补覆盖 core scheduling 下 sibling 换掉 `@prev` 的情况，并改标题。

## Maintainer 意见与讨论焦点

Andrea Righi 给出 `Reviewed-by: Andrea Righi`，并确认「separate rq->dl_server issue to be addressed in a follow-up」。他另提一个开放问题：`ops.cpu_acquire()/cpu_release()` 在 6.12 等老内核仍是受支持接口，是否考虑整体弃用（这与本补丁无关，属后续讨论）。

## 合入评估

可能性高（high）。v4 已获 Reviewer Reviewed-by，目标分支 sched_ext/for-7.4-fixes，无实质反对意见。Andrea 提及的 rq->dl_server 问题明确另起 follow-up，不阻塞本补丁。阻塞项：暂无实质阻塞；合入前需 Tejun 收尾并走 for-7.4-fixes 分支。

## 效果评估

作者用两类合成 reproducer 验证了 proxy 与 core scheduling 两种场景，未给出量化性能数据（正确性修复，无性能目标）。

## 我可以参与的点

- review：核对 `scx_dsp_prev_stale()` 在各 drop lock 点的覆盖是否完整，尤其是 sub-scheduler 嵌套 dispatch 路径。
- testing：在真实 sched_ext 调度器（scx_simple/scx_flatcg 等）上验证 core scheduling + proxy execution 组合下的稳定性。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261031162803.541236-1-tj@kernel.org/
- Andrea Righi Reviewed-by: https://lore.kernel.org/all/aubiSxuL4cEJbpU7@gpd4/
