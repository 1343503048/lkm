# sched_ext: Fix exit_task leak on fork failure during enable

## TL;DR
Tejun Heo 的补丁：当 `fork()` 失败时正确释放 `scx_task_state`，避免每进程 sched_ext 状态泄漏。已 apply 到 sched_ext。与 005/008 同属"任务退出/创建失败生命周期"健壮性议题。

## 背景与问题
sched_ext 为每个任务维护 `scx_task_state`（含 KF_mem 分配、DSQ 关联等）。若任务在 fork 过程中失败退出，`exit_task` 路径对"从未真正进入调度"的任务处理不完整，可能导致 `scx_task_state` 与 KF_mem 引用不被释放，长期累积造成内存泄漏。

## 技术方案
在 fork 失败/早期退出路径上，确保 `scx_task_state` 被释放（与正常 `exit_task` 对齐）。具体在创建失败分支调用既有释放逻辑，避免泄漏。

## 版本演进与当前进展
v1（40830）于 2026-08-15 发出，作为对 40812（早期 exit_task 修复）与 008 讨论的收尾。Tejun 自 apply。

## Maintainer 意见与讨论焦点
- Tejun Heo：直接 apply，定位为"fork 失败路径补全"，呼应 008 中"由 ops.exit_task 处理退出"的设计。

## 合入评估
已合入 sched_ext。与 008 一起确立了"任务退出清理由 BPF ops.exit_task + 内核 exit_task 兜底"的分工。

## 效果评估
修复每进程 sched_ext 状态在 fork 失败时的泄漏；无性能数据，纯资源正确性修复。

## 我可以参与的点
- 考虑补充 selftest，在 cgroup 风洞或 fork-fail 注入下验证无泄漏。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Fix exit_task leak on fork failure during enable"
id: sched-20260815-009
date: 2026-08-15
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<uid-40830@qq-imap>"
lore_url: "未获取到"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<uid-40830@qq-imap>"
    date: 2026-08-15
    summary: "fork 失败时释放 scx_task_state，避免 exit_task 资源泄漏（内存/KF_mem 引用）。"
    review_outcome: "Tejun 已 apply（'Applied to sched_ext'）。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入，等待进入 next。"
contribution_opportunities:
  - kind: testing
    description: "可写/补充 selftest 在 cgroup 风洞或 fork-fail 注入下验证无 scx_task_state 泄漏。"
generated_at: "2026-08-16T00:10:00"
source_email_count: 1
related_articles: [sched-20260815-005, sched-20260815-008]
tags: [sched_ext, crash]
---
