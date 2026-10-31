---
id: sched-20261030-011
date: 2026-10-30
subject: 'sched_ext: Fix scx_bpf_dsq_reenq() kerneldoc claiming NMI calls are allowed'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261029235251.3235814-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261029235251.3235814-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 合入 sched_ext/for-7.4-fixes
contribution_opportunities: []
generated_at: '2026-10-31T09:00:00'
source_email_count: 2
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Fix scx_bpf_dsq_reenq() kerneldoc claiming NMI calls are allowed'
layout: article
---

## TL;DR
Tejun Heo 修 sched_ext 的 kerneldoc 与实现不符：`c659e506f9a7`（"sched_ext: Reject NMI calls to lock-taking kfuncs"）已让 `scx_bpf_dsq_reenq()` 在 NMI 调用时 abort 调度器，但该 kfunc 及其 wrapper `scx_bpf_reenqueue_local___v2()` 的 kerneldoc 仍写着「Can be called from anywhere」。补丁把两处 kerneldoc 改为「任意上下文**除 NMI**」，并顺带修 wrapper 里「re-enqueue 的是 calling CPU 的 local DSQ」的错误描述（实际是 `SCX_DSQ_LOCAL` 解析到的 rq）以及 `SCX_RENQ_*` → `SCX_REENQ_*` 的拼写错误（`+8/-6`，仅文档）。Andrea Righi 已给 **Acked-by**。

## 背景与问题
纯文档一致性修复：kfunc 的实际行为（NMI 会 abort）已在 `c659e506f9a7` 改变，但 kerneldoc 未同步，导致 BPF 调度器作者可能误以为可从 NMI 安全调用。附带三处描述性错误（wrapper 的 re-enqueue 目标 DSQ、`SCX_RENQ_*` 拼写）。

## 技术方案
在 `kernel/sched/ext/ext.c` 中：
- `scx_bpf_dsq_reenq()` kerneldoc：`Can be called from anywhere` → `Can be called from any context except NMI. A call from NMI aborts the scheduler.`；`%SCX_RENQ_*` → `%SCX_REENQ_*`。
- `scx_bpf_reenqueue_local___v2()` kerneldoc：把「re-enqueue 的是 caller CPU 的 local DSQ」改为「当前调度操作所锁定的 rq 的 local DSQ（无锁时是 calling CPU 的）」，并同步排除 NMI。

无任何功能性改动，仅 `kernel/sched/ext/ext.c` 一个文件 8 增 6 删。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出）。当日获 Andrea Righi **Acked-by**（"Acked-by: Andrea Righi <arighi@nvidia.com>"）。

## Maintainer 意见与讨论焦点
- **Andrea Righi（sched_ext co-maintainer）**：Acked-by，无异议。
- 无遗留分歧。

## 合入评估
*likelihood=high*。纯文档、co-maintainer Acked、无功能风险，属 `for-7.4-fixes` 常规收取。*blocking_issues*：暂无。*next_action*：合入 `sched_ext/for-7.4-fixes`。

## 效果评估
无性能数据；纯文档一致性修复，无运行时影响。

## 我可以参与的点
当前阶段暂无明显参与空间（纯文档、已 Acked），可持续观察是否随 fixes 一并收取。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029235251.3235814-1-tj@kernel.org/
