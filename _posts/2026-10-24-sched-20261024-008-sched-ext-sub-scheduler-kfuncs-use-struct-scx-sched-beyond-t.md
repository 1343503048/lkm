---
id: sched-20261024-008
date: 2026-10-24
subject: 'sched_ext: sub-scheduler kfuncs use struct scx_sched beyond the RCU read
  side under sleepable ops'
subsystem: sched
type: bug
status: rfc
severity: high
thread_root_msgid: <tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com>
lore_url: https://lore.kernel.org/all/tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com/
authors:
- Guikun Yang
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无维护者回应
  - 无补丁、无复现确认
  next_action: Tejun/sched_ext 维护者确认问题并决定修复方式
contribution_opportunities:
- kind: discussion
  description: 分析 scx_find_sub_sched 返回对象的生命周期并回帖确认/反驳 UAF 可达性
- kind: new_patch
  description: 确认后提交修复（kfunc 持 RCU read lock/取引用，或 teardown 补 tasks-trace 同步）
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: sub-scheduler kfuncs use struct scx_sched beyond the RCU read side
  under sleepable ops'
layout: article
---

## TL;DR
Guikun Yang 报告的 sched_ext 潜在 RCU use-after-free：四个子调度器 kfunc（`scx_bpf_sub_grant/sub_revoke/sub_caps/sub_kill_bstr`）通过 `scx_find_sub_sched()`（`rhashtable_lookup()` 的 _fast 变体）拿到 `struct scx_sched *`，但 kfunc 自身只拿 `guard(irqsave)`、既不持 RCU read lock 也不对调度器取引用，却在整个函数体解引用该指针；而 sleepable struct_ops（init_task、cgroup_set_bandwidth 等）的 trampoline 只持 `rcu_read_lock_trace()`，teardown 侧又只 drain 普通 RCU（`synchronize_rcu_expedited()`，无 `rcu_tasks_trace`），导致 sleepable op 在 teardown 窗口内继续使用已释放对象。属 bug 报告、无补丁，尚无维护者回应。

## 背景与问题
`scx_bpf_sub_grant()`、`scx_bpf_sub_revoke()`、`scx_bpf_sub_caps()`、`scx_bpf_sub_kill_bstr()` 四个 kfunc 通过 `scx_find_sub_sched()` 解析子调度器，而它是 `rhashtable_lookup()` 的 _fast 变体：内部自取、自释 RCU read lock，返回的 `struct scx_sched *` 只在调用者自己的 RCU read-side 临界区内有效。但四个 kfunc 只拿 `guard(irqsave)()`（sub.c:2323），不持 RCU read lock、也不对调度器取引用，却在函数体全程解引用（如 `parent->pshard[si]`、`child->pshard[si]` 及后续加锁、`queue_sync_ecaps(child, cid)`）。它们注册在 `scx_kfunc_ids_any`（ext.c:10868），context filter 无条件放行 `in_any`，因此可从所有 sched_ext op 调用——包括 `bpf_scx_check_member()` 显式允许 sleepable 的那些（init_task、cgroup_init、cgroup_exit、cgroup_prep_move、cgroup_set_bandwidth、cpu_online、cpu_offline、init_cids、init、exit、sub_attach、sub_detach）。

关键：sleepable struct_ops 程序不持普通 RCU read lock，trampoline 只持 `rcu_read_lock_trace()` + `migrate_disable()`（kernel/bpf/trampoline.c:1446），ext.c:10567 也注明「sleepable 程序持无 RCU lock」。而 teardown 侧子调度器销毁只 drain 普通 RCU（`synchronize_rcu_expedited()`，sub.c:1626），释放经 `queue_rcu_work()` → `scx_sched_free_rcu_work()` → `scx_free_pshards()`（kfree pshard 数组）。整个 kernel/sched/ext/ 下没有 `synchronize_rcu_tasks_trace()` / `call_rcu_tasks_trace()` / `kfree_rcu_tasks`，普通 RCU 宽限期不等待 `rcu_read_lock_trace()` 临界区，故 sleepable op 在 teardown 窗口内会继续使用已释放的调度器对象。

## 技术方案
非补丁，为 bug 报告。作者给出触发序列：父调度器把 `ops.cgroup_set_bandwidth` 实现为 sleepable 程序，其调用者 `scx_group_set_bandwidth()`（ext.c:5044）只持 `scx_cgroup_ops_rwsem`（非 `scx_enable_mutex`），可与子调度器 teardown 并发；该 op 调 `scx_bpf_sub_grant()` 解析 child 后全程解引用，同时子调度器被 teardown（`scx_bpf_sub_kill_bstr()` → `scx_exit_bstr()`，或 `scx_bpf_exit()`、`scx_error()`）。作者未附修复补丁，仅列出问题链路与涉及代码位置。

## 版本演进与当前进展
*current_version: null*。非补丁系列，为 bug 报告（`<tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com>`），当日发出、无回应。

## Maintainer 意见与讨论焦点
无维护者表态。报告直接写给 Tejun Heo（"Hi Tejun"），问题定位细致（含行号与两条 RCU drain 路径对比），等待 Tejun 或 sched_ext 维护者确认是否属实及修复方向。

## 合入评估
*likelihood=unknown*。这是针对 sched_ext 子调度器 kfunc 的潜在 RCU UAF 报告、非补丁，且无维护者回应；需 Tejun 确认并给出修复（例如 kfunc 内自持 RCU read lock、对调度器取引用、或 teardown 侧加 `rcu_tasks_trace` 同步）。*blocking_issues*：无回应、无补丁、无复现确认。*next_action*：Tejun/sched_ext 维护者确认问题并决定修复方式。

## 效果评估
无数据。报告为静态/机制层分析（RCU read lock 与 `rcu_read_lock_trace()` 的宽限期不匹配），未提供实际触发/崩溃复现。

## 我可以参与的点
- *kind: discussion*：分析 `scx_find_sub_sched()` 的返回对象生命周期，确认在 sleepable op 中是否确有可触发的 UAF，并回帖提供复现或反驳依据。
- *kind: new_patch*：若确认属实，可提交修复（kfunc 内持 RCU read lock 或对 scx_sched 取引用，或 teardown 侧补 tasks-trace 同步）。

## 参考链接
- 报告: https://lore.kernel.org/all/tencent_572AA31E5369BE41464E9DDA4CEDA2DA7C09@qq.com/
