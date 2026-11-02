---
type: fix
status: under_review
severity: high
thread_root_msgid: <20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org>
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org>
  date: '2026-11-01'
  summary: 验证期拒绝 tracing 程序调用 scx_bpf_destroy_dsq()
  review_outcome: 暂无 review
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Tejun 收取进 sched_ext fixes 分支
contribution_opportunities:
- kind: review
  description: 审计 scx_kfunc_ids_any 中其它取锁 kfunc 是否同样暴露给 tracing
- kind: testing
  description: 用混插 FIFO/pq 的 user DSQ 调度器复现死锁并验证修复
upstream_commit: null
fixes_commit: f0e1a0643a59
merged_branch: null
source_email_count: 1
related_articles: []
tags:
- sched_ext
- bpf
- hang
id: sched-20261102-008
subject: 'sched_ext: Reject scx_bpf_destroy_dsq() in tracing programs'
date: '2026-11-02'
subsystem: sched
generated_at: '2026-11-03T01:22:31'
lore_url: null
title: 'sched_ext: Reject scx_bpf_destroy_dsq() in tracing programs'
layout: article
---

## TL;DR

Shubhang Kaushik（Ampere）修复 sched_ext 的一个死锁：`scx_bpf_destroy_dsq()` 会取目标 user DSQ 的 raw spinlock，却也被注册到 `BPF_PROG_TYPE_TRACING`（`scx_kfunc_ids_any`）。一个未关联的 tracing 程序可经兼容路径解析到活动 root 调度器，在 DSQ 锁已被持有时递归 `scx_bpf_destroy_dsq()` 死锁 CPU。修复为在验证期拒绝 tracing 程序调用该 kfunc。`Fixes: f0e1a0643a59`。

## 背景与问题

`scx_bpf_destroy_dsq()` 取目标 user DSQ 的 raw spinlock。但它位于 `scx_kfunc_ids_any`，也注册给了 `BPF_PROG_TYPE_TRACING`。对无 `ops.sub_attach` 的活动 root 调度器，`scx_prog_sched()` 的兼容路径会让未关联的 tracing 程序解析到该调度器；tracing 程序于是能在 DSQ 锁已被持有时调用 `scx_bpf_destroy_dsq()`。典型链路：混用 FIFO 与 priority-queue 插入同一 user DSQ 的调度器在 `scx_dispatch_enqueue()` 持锁时触发 `scx_error()` → `scx_claim_exit()` → `trace_sched_ext_exit` → tracing BPF → `scx_bpf_destroy_dsq()` → `raw_spin_lock_irqsave(&dsq->lock)` 同一把锁，递归自锁锁死 CPU；且 tracepoint 在 `scx_finish_exit()` 之前运行，`disable_irq_work` 未入队、调度器无法进入正常 disable 路径。

## 技术方案

在验证期拒绝 tracing 程序调用 `scx_bpf_destroy_dsq()`（`kernel/sched/ext/ext.c`，+4）；kfunc 仍对 SCX struct_ops 与 syscall 程序可用。

## 版本演进与当前进展

v1（2026-11-01），暂无 review。

## Maintainer 意见与讨论焦点

尚无表态；属 sched_ext 安全/死锁修复，`Fixes: f0e1a0643a59`（sched_ext BPF 类实现）。

## 合入评估

likelihood=high。调用路径清晰、修复在验证期最小化、有 Fixes 标签；预期 Tejun 会收进 sched_ext/for-7.4-fixes（或类似分支）。

## 效果评估

作者给出死锁调用链（递归获取同一 raw spinlock），未附独立数值数据。

## 我可以参与的点

- review：确认 `scx_kfunc_ids_any` 里是否还有其它取锁 kfunc 同样暴露给 tracing 程序。
- testing：复现 FIFO+pq 混插 user DSQ 的调度器在 tracing 程序下的死锁，验证修复后不再锁死。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org/
