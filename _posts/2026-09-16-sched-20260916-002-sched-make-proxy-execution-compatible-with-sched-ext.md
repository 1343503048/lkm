---
id: sched-20260916-002
date: '2026-09-16'
subject: 'sched: Make proxy execution compatible with sched_ext'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260831134338.1531664-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- John Stultz
current_version: v13
patch_series:
- version: v13
  msgid: <20260831134338.1531664-1-arighi@nvidia.com>
  date: '2026-08-31'
  summary: 18 枚补丁，sched_ext 与 proxy execution 兼容
  review_outcome: Peter 09-16 正式评审，Andrea 准备 v14 落实 05/07/09/14/15 改动，08/18 语义待定
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 08/18 WF_ON_RQ 语义需重新定义或按 Peter 的 is_blocked 重构思路
  - 09/18 清理时机重构需验证 sched_ext enable / ownership-transition 路径
  next_action: Andrea 发 v14 落实改动，与 Peter 对齐 08/18 方向
contribution_opportunities:
- kind: review
  description: 从 PELT/psi 记账角度评估 08/18 两种方案的副作用
- kind: discussion
  description: 分析 07/18 reject-DSQ 重试是否有更早的触发时机
generated_at: '2026-09-17T09:00:00'
source_email_count: 14
related_articles:
- sched-20260910-002
tags:
- proxy_execution
- sched_ext
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR
本日为增量更新：Peter Zijlstra 对 Andrea Righi 的 proxy-execution 兼容 sched_ext 系列（v13，18 枚）逐 patch 正式评审，焦点集中在 08/18 的 `WF_ON_RQ` 语义（Andrea 自己承认「描述错了区分」）以及 07/18 的 reject-DSQ 重试点设计。Andrea 已在多枚 patch 上给出回应并准备 v14，暂无 NAK，但 08/18 的方向仍有开放讨论（Peter 抛出了一个未测试的 `sched_delayed`→`is_blocked` 大重构思路）。合入可能性维持中等。完整背景见 related_articles。

## 背景与问题
该系列的目标是让 proxy execution（拆分执行上下文与调度上下文）与 sched_ext 兼容：sched_ext 需要感知 proxy 带来的 donor/curr 分离、blocked donor 的 runqueue 驻留、以及任务在 EXT 调度类与其它类之间切换时的清理时机。背景与前几版一致，见 sched-20260910-002。

## 技术方案
系列核心机制不变。本日讨论落在三处具体设计：
- **07/18**（`scx_proxy_resolved()`，Andrea 拟改名 `scx_proxy_reenqueue_retry()`）：当 sched_ext 消费从远程 DSQ dispatch 来的任务时，若 proxy exec 已使该任务成为 rq->curr 或 active donor，则无法迁移，需把任务 park 到源 rq 的 reject DSQ，并在下一次 proxy selection 后重试 drain。
- **08/18**（`WF_ON_RQ`）：sched_ext 需要知道「这次 wakeup 是否走了 `ttwu_runnable()` 而没调用 activate/enqueue」。Andrea 承认 `WF_ON_RQ` 命名/语义不准确。
- **09/18**：把 `sched_proxy_block_task()` 的清理从 `sched_change_begin()` 移到 sched_ext 的 ownership-transition 路径（`sched_change_begin()` 之前），否则 `ctx->queued` 会在切换 EXT 时被错误记为 true。

## 版本演进与当前进展
- **v13**（2026-08-31，`<20260831134338.1531664-1-arighi@nvidia.com>`）：当前版本。
- 本日（09-16）Peter 正式评审 04/05/07/08/09/14/15，Andrea 逐条回应并承诺 v14 改动：05/18 删除并改为对 `DEQUEUE_CLASS` 条件处理；07/18 改名并补充说明；09/18 移到 ownership-transition 路径；14/18 删掉两个「possible combinations」条目并显式声明 invariant；15/18 inline 化 `scx_allow_proxy_exec()` 包装（用 `scx_enabled()` 静态 key）。04/18 已抽为独立修复单发（见 sched-20260916-001）。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（07/18）**：质疑为何不把 blocked 任务直接留在 reject 队列、等 wakeup 再处理。Andrea 解释：被 reject 的任务未必 blocked——一个 runnable 的 EXT mutex owner 正通过 blocked donor 的调度上下文在 CPU0 执行，其 EXT entity 仍可能在非本地 DSQ；CPU1 并发消费它时发现它已是 rq->curr 无法迁移，park 后若无重试点，它就不再对 BPF 调度器可见、永远无法用自己的调度上下文运行。
- **Peter Zijlstra（08/18）**：提出一个 *COMPLETELY UNTESTED* 的大方向——把核心里 `p->se.sched_delayed` 的用法替换为 `p->is_blocked`，并给 class 方法引入 `{EN,DE}QUEUE_BLOCKED`，认为这也许能让 ext 直接做正确的事。Prateek 追问具体 class 语义，并建议在 `sched_class->flags` 里加允许的 flags bitmap；Peter 表示「考虑过多次但没动手，有用的话可以」。
- **John Stultz（08/18）**：建议干脆在 `proxy_needs_return()` 里去掉 `task_cpu(p) == p->wake_cpu` 短路（或按 sched_class 条件化），也许比引入新 flag 更简单。
- 分歧点：08/18 的 `WF_ON_RQ` 方案与「用 `is_blocked` + `{EN,DE}QUEUE_BLOCKED` 重构」两条路线尚未定论，属于需要进一步讨论的开放项。

## 合入评估
likelihood=medium。系列方向被认可、无 NAK，Andrea 积极回应并已在收敛 v14；但 08/18 涉及核心唤醒路径语义与一个潜在的大重构方向，Peter 自己也标注「未测试」「可能是 pain in the arse」，短期内难以全部落地。blocking_issues：08/18 `WF_ON_RQ` 语义需重新定义或按 Peter 思路重构；09/18 清理时机重构需验证 sched_ext enable / ownership-transition 两条路径。next_action：Andrea 发 v14 落实上述改动，08/18 方向与 Peter 对齐。

## 效果评估
本日讨论未涉及性能数据，属设计评审与正确性论证。

## 我可以参与的点
- kind=review：对 08/18 两种方案（`WF_ON_RQ` vs `is_blocked`+`{EN,DE}QUEUE_BLOCKED`）从 PELT/psi 记账角度评估副作用，Prateek 已指出 proxy donor 情况下 `psi_enqueue()` 会双记账的隐患，可深入验证。
- kind=discussion：分析 07/18 reject-DSQ 重试点是否有更早的触发时机可替代「下一次 proxy selection 后」的延迟 drain。

## 参考链接
- v13 cover：https://lore.kernel.org/all/20260831134338.1531664-1-arighi@nvidia.com/
- Peter 对 08/18 的重构草案：https://lore.kernel.org/all/20260916091908.GG4121339@noisy.programming.kicks-ass.net/
- 07/18 reject-DSQ 讨论：https://lore.kernel.org/all/20260916090017.GF4121339@noisy.programming.kicks-ass.net/
