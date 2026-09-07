---
id: sched-20260902-006
date: '2026-09-02'
subject: 'sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Wanwu Li
- liwanwu
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: high
  blocking_issues:
  - 'Tejun Heo 对 scx_task_sched_rcu(p) ?: sch 这组 fallback 表达式的意见未落实'
  - 可达性论证（never-enabled 任务）尚无独立复现或 Tested-by
  next_action: 按 Tejun 意见出 v3，并在带 sub-sched 的 scx 分层环境下给出复现与 Tested-by
contribution_opportunities:
- 在带 sub-sched 的 scx 分层配置下复现 never-enabled 任务触发路径，验证可达性论证
- 推动本处 fallback 与 004 的 scx_kf_allowed_ctx() 统一为同一个 task->sched 反查 helper
- 给 v2/v3 补 Tested-by，目前该线程无任何正式 tag
source_email_count: 3
related_articles: []
tags:
- sched_ext
- crash
title: 'sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path'
layout: article
---

## TL;DR

sched_ext 的 COMPAT kfunc 包装在 root scheduler 挂了 sub-sched 时会对 NULL 的 `p->scx.sched` 调
`scx_error()`。补丁 9/2 23:36 发出，十几个小时内两位 sched_ext 维护者全部回帖并已出 v2（范围扩大）。
推进极快，跟进成本低。

## 背景与问题

`sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
指针做充分空值检查，导致在错误分支上解引用空指针（NULL deref）崩溃（UID 74497）。

## 技术方案

- `sched_ext: Fix NULL sched deref in select_cpu_and sub-sched error path`：在
  select_cpu_and 的子调度错误返回路径上补上空指针判断，避免解引用空 `sched`。

## 版本演进与当前进展

- 当前状态：**under_review**（新补丁）。
- 严重度：**high**（空指针解引用属崩溃类 bug）。
- 合入可能性 medium/high；属明确的小修复。

## Maintainer 意见与讨论焦点

- Andrea Righi 9/3 00:14 第一个接手并确认了崩溃与方向（74645）；作者 liwanwu 74707 直接认漏："This one
  is my miss: I reasoned about scx_bpf_dsq_insert_vtime() from the SYSCALL rejection alone …" —— 因此 v2
  （74871）标题从 `in select_cpu_and sub-sched error path` 改成 `in kfunc sub-sched error paths`，把
  `scx_bpf_select_cpu_and()` 和 `scx_bpf_dsq_insert_vtime()` 两个包装一起修。
- Tejun Heo 9/3 连回两条（75131/75110）：一方面接受可达性论证——作者主张 "Neither wrapper requires a
  contrived @p. Tasks that are never enabled -- kthreads and tasks of other classes under SCX_SWITCH_ALL=n…"；
  另一方面对写法提出质疑，针对 `scx_error(scx_task_sched_rcu(p) ?: sch, …)` 说 "As the fallback only
  triggers for tasks a…"（缓存中截断）。
- 无 NAK；分歧集中在 fallback 该取哪个 sched，而不是该不该修。

## 合入评估

**高**。崩溃类、两位维护者都已确认方向、v2 已出，预计收敛后直接进 sched_ext 树。卡点仅两个：Tejun 对
`scx_task_sched_rcu(p) ?: sch` 这个 fallback 表达式的意见未落实；v2 之后尚无 v3，也没有任何 Tested-by/
Reviewed-by。

## 效果评估

Andrea Righi 确认了 crash 存在（作者原话 "Thanks for picking this up so quickly, and for confirming the
crash and the fix direction."），但缓存中没有留下栈、复现脚本或影响范围的细节。无性能数据。

## 我可以参与的点

- 实测 Tejun 关心的可达性：在带 sub-sched 的 scx 分层配置下，用 never-enabled 任务（kthread、
  `SCX_SWITCH_ALL=n` 时其它调度类任务）跑这两个 COMPAT kfunc，给出真实触发结论。
- 把这里的 `scx_task_sched_rcu(p) ?: sch` 与 004 的 `scx_kf_allowed_ctx()` 放一起看——两者都在解决
  「task→sched 反查可能拿不到 sched」，应该统一成一个 helper。
- v2 之后无人再回帖推动，可以直接给 Tested-by。

## 参考链接

- 004 sched_ext：拒绝 NMI 调用会拿锁 kfuncs
- 005 sched_ext：文档化并强制 vtime 排序约束
