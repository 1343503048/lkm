---
id: sched-20261027-011
date: 2026-10-27
subject: 'sched_ext: Reject rq-lock-taking kfuncs in tracing programs'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261027051634.2009082-1-sprooc69@gmail.com>
lore_url: https://lore.kernel.org/all/20261027051634.2009082-1-sprooc69@gmail.com/
authors:
- Junbin Zhang
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261027051634.2009082-1-sprooc69@gmail.com>
  date: 2026-10-27
  summary: 新增 scx_kfunc_ids_no_tracing，verifier 阶段拒绝 tracing 程序调用 cpuperf/cidperf
    kfunc
  review_outcome: 无当日 review
upstream_commit: null
fixes_commit: a11d6784d731
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 需 sched_ext 维护者确认拒绝集合与 filter 逻辑
  next_action: 等 Tejun 或相关 reviewer 收取
contribution_opportunities:
- kind: review
  description: 核对 scx_kfunc_ids_any 里是否还有同类 rq-lock 风险 kfunc
- kind: testing
  description: 复现死锁并验证补丁后 tracing 调用被 verifier 拒绝
generated_at: '2026-10-28T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Reject rq-lock-taking kfuncs in tracing programs'
layout: article
---

## TL;DR
Junbin Zhang（sprooc）发单补丁修一个死锁：`scx_bpf_cpuperf_set()`/`scx_bpf_cidperf_set()` 注册在 `scx_kfunc_ids_any`（对 `BPF_PROG_TYPE_TRACING` 开放），而 tracing 程序可能运行在「外层已持 rq lock」的上下文（如 `sched_switch`），此时 kfunc 会再次 `rq_lock_irqsave()` 拿同一把锁、锁死 CPU。补丁在 verifier 阶段拒绝 tracing 程序调用这两个 kfunc，同时保留 struct_ops 与 syscall 程序的访问。当日新发，尚无维护者回应。

## 背景与问题
`scx_locked_rq()` 只跟踪「SCX 回调调用期间」持有的 rq lock，无法探测外层内核代码已持有的 rq lock。于是 `tp_btf/sched_switch` 这类 tracing 程序在 `__schedule()` 的 `rq_lock()` 之后触发，`scx_bpf_cpuperf_set(smp_processor_id(), 1024)` 会走 `scx_cpuperf_set()` 的解锁路径再次 `rq_lock_irqsave()` 拿同一把锁，lockdep 报递归锁死锁，CPU 带关中断锁死。`scx_bpf_cidperf_set()` 同样受影响。作者用「最小 SCX 调度器 + tp_btf/sched_switch tracing 程序」两个 BPF 程序即可复现。`Fixes: a11d6784d731`。

## 技术方案
单补丁（`kernel/sched/ext/ext.c` +19/−1）：新增 `scx_kfunc_ids_no_tracing` 集合，把 `scx_bpf_cpuperf_set`、`scx_bpf_cidperf_set` 两个会取 rq lock 的 kfunc 收进去，并在 `scx_kfunc_context_filter()` 里对非 STRUCT_OPS 程序（tracing/syscall 等）追加 `!in_no_tracing` 拒绝条件。两个 kfunc 仍保留在 `scx_kfunc_ids_any` 中以供 struct_ops 与 syscall 程序使用。作者判断「无法可靠判断 tracing 上下文是否已持 rq lock」，故只能在验证期一刀切拒绝。

## 版本演进与当前进展
*current_version: v1*（`<20261027051634.2009082-1-sprooc69@gmail.com>`），当日新发。

## Maintainer 意见与讨论焦点
当日无维护者回应。

## 合入评估
*likelihood=high*。带 `Fixes:`、完整死锁复现与 lockdep 栈，属清晰正确性修复，方向（验证期拒绝）合理。*blocking_issues*：需 sched_ext 维护者（Tejun Heo）review 确认拒绝集合与 filter 逻辑。*next_action*：等 Tejun 或相关 reviewer 收取。

## 效果评估
作者给出完整复现（两个 BPF 程序 + lockdep 递归锁 WARN 栈）。未附修复后的验证数据，但改动面小、逻辑明确。

## 我可以参与的点
- *kind: review*：核对是否还有其它 `scx_kfunc_ids_any` 里的 kfunc 存在同类「外层已持 rq lock」风险。
- *kind: testing*：复现该死锁并验证补丁后 tracing 程序调用被 verifier 拒绝。

## 参考链接
- patch: https://lore.kernel.org/all/20261027051634.2009082-1-sprooc69@gmail.com/
