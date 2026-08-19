# sched_ext: Dispatch path follow-ups

## TL;DR
Tao Cui 的 v2 patch：当目标 DSQ 已被 `scx_task_exit()` 销毁时，`scx_dispatch()`/consume 不再 `BUG_ON` 直接 panic，而是立即返回。避免任务退出竞态触发的内核崩溃。与 009 系列（exit_task 资源泄漏）同根因、互补。

## 背景与问题
`sched_ext` 任务退出时 `scx_task_exit()` 会销毁其关联的 DSQ。若另一 CPU 同时仍在该 DSQ 上执行 `scx_dispatch()`/consume，会因 DSQ 已被标记销毁而触发 `BUG_ON`，造成内核 panic（崩溃）。属于任务退出竞态下的健壮性 bug。

## 技术方案
v2 改动：在 `scx_dispatch()` 与 consume 路径中，先检查目标 DSQ 是否已进入销毁态；若是，立即返回而非 `BUG_ON`。并引入"task gone"信号抢占点。相比 v1 更细化地避免 panic 同时保留语义正确。

## 版本演进与当前进展
- v1 (`<174978258713.40806-1-...>`)：首版，Andrea Righi 给出 `Reviewed-by: Andrea Righi <...>`。
- v2 (`41198`)：修订版，2026-08-15 发出，细化"task gone"信号抢占逻辑。
Tejun 在相关讨论（见 008/009）倾向"由 BPF 侧通过 `ops.exit_task` 处理"而非内核兜底，本系列走向需待其最终表态。

## Maintainer 意见与讨论焦点
- Andrea Righi：v1 Reviewed-by。
- Tejun Heo：在关联线程指出任务退出时应由 `ops.exit_task` 让 BPF 调度器自行处理；暗示可能更偏好 BPF 侧修复（见 009 系列），但 005 的内核健壮性兜底仍可能被收下。

## 合入评估
合入可能性高（已有 R-by），但与 009 的讨论交织：Tejun 倾向让 `ops.exit_task` 承担更多退出清理。需确认 005 的 BUG_ON→return 兜底与 exit_task 资源回收无冲突。

## 效果评估
消除一类任务退出竞态导致的 `BUG_ON` 内核 panic；无性能数据，纯健壮性修复。

## 我可以参与的点
- 评审 v2 的"task gone"抢占点是否覆盖全部 `scx_dispatch`/consume 路径；与 009 是否互补而非重复。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched_ext: Dispatch path follow-ups"
id: sched-20260815-005
date: 2026-08-15
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<uid-41198@qq-imap>"
lore_url: "未获取到"
authors: [Tao Cui]
maintainers_involved: [Tejun Heo]
current_version: v2
patch_series:
  - version: v2
    msgid: "<uid-41198@qq-imap>"
    date: 2026-08-15
    summary: "scx_dispatch()/consume 立即返回而非对已被 scx_task_exit() 销毁的 DSQ 触发 BUG_ON。"
    review_outcome: "v1 已获 Andrea Righi Reviewed-by；v2 修订中，等待 Tejun 最终确认。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: [与 008/009 系列讨论 'task gone' 信号语义，需确认 005 与 009 的修复是否重复/互补]
  next_action: "等待 Tejun 对 v2 的最终确认（其倾向用 ops.exit_task 由 BPF 侧处理）。"
contribution_opportunities:
  - kind: review
    description: "评审 v2 的 'task gone' 信号抢占点是否覆盖了所有 scx_dispatch/consume 路径，且与 009 的 exit_task 修复不冲突。"
generated_at: "2026-08-16T00:10:00"
source_email_count: 2
related_articles: [sched-20260815-009]
tags: [sched_ext, crash]
---
