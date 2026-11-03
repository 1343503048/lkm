# sched_ext: Reject scx_bpf_destroy_dsq() in tracing programs

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261102-008：Shubhang Kaushik（Ampere）修复 sched_ext 死锁：`scx_bpf_destroy_dsq()` 取目标 user DSQ 的 raw spinlock，却也被注册给 `BPF_PROG_TYPE_TRACING`，未关联的 tracing 程序可在 DSQ 锁已持有时递归调用该死锁；修复为验证期拒绝 tracing 程序调用该 kfunc（`Fixes: f0e1a0643a59`）。
- sched-20261103-024（今天）：Tejun Heo 已把补丁收进 sched_ext/for-7.4-fixes。

## 背景与问题

（承接 sched-20261102-008）`scx_bpf_destroy_dsq()` 位于 `scx_kfunc_ids_any`、也注册给 `BPF_PROG_TYPE_TRACING`；无 `ops.sub_attach` 的活动 root 调度器经 `scx_prog_sched()` 兼容路径让未关联 tracing 程序解析到该调度器，在 DSQ 锁已持有时调用 `scx_bpf_destroy_dsq()` 自锁死 CPU。今日无新代码。

## 技术方案

（承接）验证期拒绝 tracing 程序调用 `scx_bpf_destroy_dsq()`（+4），kfunc 仍对 SCX struct_ops 与 syscall 程序可用。今日为收取确认。

## 版本演进与当前进展

*current_version: v1（已合入）*。今日 Tejun 回 Applied：「Applied to sched_ext/for-7.4-fixes」。

## Maintainer 意见与讨论焦点

无分歧；属 sched_ext 安全/死锁修复，Tejun 当日收取。

## 合入评估

*likelihood=merged*。已进 sched_ext/for-7.4-fixes（`Fixes: f0e1a0643a59`，预期随 scx 树进 tip 并回合 stable）。

## 效果评估

无性能数据；属死锁/安全问题修复。

## 我可以参与的点

当前阶段暂无明显参与空间；可关注其后续进 tip 与 stable 回合。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org/

---
id: sched-20261103-024
date: 2026-11-03
subject: "sched_ext: Reject scx_bpf_destroy_dsq() in tracing programs"
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: "<20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org>"
lore_url: "https://lore.kernel.org/all/20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org/"
authors: ["Shubhang Kaushik (Ampere)"]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261101-scx-destroy-dsq-tracing-v1-1-987a7f2f5bec@gentwo.org>"
    date: 2026-11-01
    summary: "验证期拒绝 tracing 程序调用 scx_bpf_destroy_dsq()，防死锁。"
    review_outcome: "已收进 sched_ext/for-7.4-fixes。"
upstream_commit: null
fixes_commit: "f0e1a0643a59"
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 scx 分支，关注进 tip 与 stable 回合。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-008]
tags: [sched_ext]
---