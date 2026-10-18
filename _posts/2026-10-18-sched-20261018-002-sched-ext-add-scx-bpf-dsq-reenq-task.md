---
id: sched-20261018-002
date: 2026-10-18
subject: 'sched_ext: Add scx_bpf_dsq_reenq_task()'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20261017223738.993262-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261017223738.993262-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261017223738.993262-1-tj@kernel.org>
  date: 2026-10-17
  summary: 新增 scx_bpf_dsq_reenq_task() kfunc 只重入队 DSQ 迭代中被标记的任务；qmap 改用新 kfunc
  review_outcome: Andrea Righi 三枚 Reviewed-by，附掉锁周期/跨 CPU mark/异调度器三项非阻塞意见
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已应用 sched_ext/for-7.4，随 7.4 合入窗口进主线
contribution_opportunities:
- kind: extend
  description: 打磨跨 CPU 并发迭代同一 DSQ 的 mark 归属说明，及 scx_error() 后异调度器任务返回 false 的边界
- kind: testing
  description: 在 CONFIG_EXT_SUB_SCHED + caps 撤销场景实测新 kfunc 的 marked 重入队与保位语义
generated_at: '2026-10-19T09:00:00'
source_email_count: 10
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Add scx_bpf_dsq_reenq_task()'
layout: article
---

## TL;DR

Tejun Heo 发往 `sched_ext/for-7.4` 的三补丁系列：新增 `scx_bpf_dsq_reenq_task()` kfunc，让 BPF 调度器能只把 DSQ 迭代中「被标记」的单个任务重入队（此前 `scx_bpf_dsq_reenq()` 只能整队重入队、`scx_bpf_dsq_move()` 是选位而非重入队），解决 caps 撤销后只需重新放置被卡任务（而非全队）的场景。Andrea Righi 三枚均 `Reviewed-by`，Tejun 已应用 1–3 到 `sched_ext/for-7.4`。

## 背景与问题

一个丢失了服务某 DSQ 的 CPU 的调度器，需要把卡在该 DSQ 上的任务重新放置——且只放这些。`scx_bpf_dsq_reenq()` 重入队整个 DSQ：每个任务都重新走一遍 `ops.enqueue()` 并被重新选位、重排。唯一的逐任务原语 `scx_bpf_dsq_move()` 是「选位决策」而非「重入队」。caps 撤销后清扫自己 DSQ 的 sub-scheduler 正是这类调用者。

## 技术方案

三补丁（`kernel/sched/ext/`）：

- **1/3 `Factor out the rq lock switch of scx_dsq_move()`**：从 `scx_dsq_move()` 抽出 rq 锁切换，新 kfunc 可共用。
- **2/3 `Add scx_bpf_dsq_reenq_task() to re-enqueue single tasks from a DSQ iteration`**：新 kfunc 标记 DSQ 迭代中的某任务；迭代结束时 DSQ 的 deferred re-enqueue walk 被调度一次，只以 DSQ 顺序、带 `SCX_ENQ_REENQ` 重入队被标记任务，其余任务保持原位。kfunc 像 `scx_bpf_dsq_move()` 一样锁任务 rq 与 DSQ，可从相同上下文调用；标记在任务离开 DSQ 时清除，故 walk 前已被消费的任务不会被重入队。
- **3/3 `scx_qmap: Also re-enqueue stranded tasks with scx_bpf_dsq_reenq_task()`**：让 scx_qmap 用新 kfunc 重入队卡在其 shared DSQ 上的部分任务（而非移到 rescue 路径），从而两个 kfunc 都被实际行使。这些任务重新走 `ops.enqueue()` 被 rescue，其余排队任务保位。

基于 `sched_ext/for-7.4`（9c0af54cb49c），git 分支 `dsq-reenq-task`。

## 版本演进与当前进展

*current_version: v1*（系列无版本号；2/3 有 v2）。

- v1（2026-10-17 发，2026-10-18 北京收）：三补丁如上。
- 2/3 有 v2（`20261017233508.1276329-1-tj@kernel.org`）：作为对原 2/3 的回复贴出，被 Tejun 应用时采用。

## Maintainer 意见与讨论焦点

Andrea Righi（sched_ext 维护者）三枚均 `Reviewed-by`，2/3 附带三条非阻塞意见：

- **IRQs off 长锁**：`SCX_REENQ_MARKED` 下 `reenq_user()` 可能返回 false 并跳过任务，但仍持 dsq->lock（与 rq 锁、IRQs 关闭）。任务很多时意味着开着 IRQs off 遍历全体；建议后续「计数已访问任务、周期性掉 dsq->lock」（cursor 保位）——这正是 Tejun 后来单独补丁 `Drop the locks periodically...`（本日另一篇）的由来。
- **跨 CPU 迭代的 mark 归属**：两 CPU 并发迭代同一 DSQ 时，一方排的 walk 可能在另一方迭代结束前就重入队其标记的任务——无害，但建议加一句说明。
- **不同调度器的任务**：`scx_error()` 后 `@p` 属于不同调度器时也应返回 false。

3/3 一处 nit：`if ((p->pid & 1) && __COMPAT_has_dsq_reenq_task())`。Tejun 澄清 scx_qmap 已是 7.4-only（实现了 `ops.sub_cid_sched_updated()`/`ops.sub_child_ecaps_updated()`，旧内核没有），干脆把 qmap 里所有 compat 残留都拆掉、默认配对最新内核；Andrea 认同「拆掉兼容位是好事」。

## 合入评估

*likelihood=merged*。Tejun 已应用 1–3 到 `sched_ext/for-7.4`（2/3 采用 v2），并给 1、3 追加 `Reviewed-by: Andrea Righi`。*blocking_issues*：无（意见均为非阻塞，后续化为独立锁周期补丁）。*next_action*：随 for-7.4 进 7.4 合入窗口。

## 效果评估

无 benchmark 数字。3/3 让 scx_qmap 实际行使新 kfunc，属功能自测性质；「其余排队任务保位」是相对整队重入队的语义收益，未见量化数据。

## 我可以参与的点

- `extend`：Andrea 提出的「周期性掉 dsq->lock（计数访问任务、cursor 保位）」已由 Tejun 单独成补丁（见本日 `Drop the locks periodically...`），但「跨 CPU 并发迭代同一 DSQ 的 mark 归属」说明与「不同调度器任务返回 false」的边界可继续打磨。
- `testing`：在启用 `CONFIG_EXT_SUB_SCHED` 子调度器 + caps 撤销场景下实测新 kfunc，确认 marked 任务按 DSQ 序重入队、未标记任务保位。

## 参考链接

- 系列封面信：https://lore.kernel.org/all/20261017223738.993262-1-tj@kernel.org/
- 2/3 v2：https://lore.kernel.org/all/20261017233508.1276329-1-tj@kernel.org/
- Tejun 应用确认：https://lore.kernel.org/all/79fb573898f66c7a107514e87e16c68e@kernel.org/
