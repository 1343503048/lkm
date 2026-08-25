# Tejun Heo 修复 `scx_bpf_dsq_move()` 中的虚假调度器中止：任务在迭代过程中可能合法地失去所有权（退出或被重新分配）

## TL;DR

Tejun Heo 修复 `scx_bpf_dsq_move()` 中的虚假调度器中止：任务在迭代过程中可能合法地失去所有权（退出或被重新分配），但早期所有权检查将这些良性竞态升级为调度器中止。修复将所有权检查移到 cursor-lost 检查之后。已合入 `sched_ext/for-7.3-fixes`。

## 背景与问题

`scx_dsq_move()` 在获取锁之前验证任务是否属于调用调度器，不匹配时中止调度器。但任务可以在任何时刻失去调度关联：完全退出清除关联，或被重新分配到其他子调度器。这些都是良性竞态，但早期所有权检查将它们升级为调度器中止。

Fixes 标签指向 `bb4d9fd55158 ("sched_ext: scx_dsq_move() should validate the task belongs to the right scheduler")`。

## 技术方案

将所有权检查移到 cursor-lost 检查之后。在锁下仍然在迭代 DSQ 上的任务但被其他地方拥有，才表示真正的违规并应中止。同时修复两个引用旧名称 `sched_ext_free()` 的过时注释（已改名为 `sched_ext_dead()`）。

## 版本演进与当前进展

v1 已合入 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点

已合入，无争议。

## 合入评估

- **likelihood**: merged
- 已合入 `sched_ext/for-7.3-fixes`

## 效果评估

消除虚假中止，提升 SCX 调度器稳定性。

## 我可以参与的点

当前阶段暂无明显参与空间，补丁已合入。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260822-004
date: 2026-08-22
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<7b3b7e35d462fe061105f09de3a2eba9@kernel.org>"
lore_url: "未获取到"
authors: ["Tejun Heo"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<7b3b7e35d462fe061105f09de3a2eba9@kernel.org>"
    date: 2026-08-22
    summary: "修复 scx_bpf_dsq_move() 虚假中止，将所有权检查移到 cursor-lost 检查之后"
    review_outcome: "已合入 sched_ext/for-7.3-fixes"
upstream_commit: null
fixes_commit: "bb4d9fd55158"
merged_branch: "sched_ext/for-7.3-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入"
contribution_opportunities: []
generated_at: "2026-08-22T10:00:00"
source_email_count: 1
related_articles: []
tags: ["sched_ext", "bpf"]
---
