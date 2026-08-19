# sched/numa: Fix scan period for remote private faults

# sched/topology: NUMA 掩码分配失败时释放

## TL;DR
`sched_domains_numa_masks` 在部分分配失败时未释放已分配掩码，存在错误路径泄漏。Hongling Zeng 补上清理。低严重度清理，属 medium（需确认与其它 topology 清理的合并）。

## 背景与问题
构建 NUMA 调度域时会为各 node 分配 `sched_domains_numa_masks`，若中间某一层分配失败，已分配的部分掩码不会被释放，造成内存泄漏与状态不一致。该路径触发概率低（仅在内存紧张/node 数多时），但属正确性清理。

## 技术方案
在分配失败回滚路径中，释放此前已成功分配的掩码数组。同作者在 19062 还讨论了 topology 构建失败的其它清理点，可能需要统一处理。

## 版本演进与当前进展
v1（2026-08-04），作者 Hongling Zeng。

## Maintainer 意见与讨论焦点
尚未见 maintainer 回复。焦点可能与 19062 的 topology 清理合并。

## 合入评估
合入可能性 medium。低频错误路径清理，需确认与 19062 是否合并处理，无功能风险。

## 效果评估
无基准；属错误路径内存泄漏修复，效果以「无泄漏」衡量。

## 我可以参与的点
- 可审计 sched domain 构建失败回滚中是否还有其它未释放的 per-node 分配，回帖补充（与 19062 合并）。

## 参考链接
- lore thread: 未获取到

---
subject: "sched/numa: Fix scan period for remote private faults"
id: sched-20260804-012
date: 2026-08-04
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Hongling Zeng]
maintainers_involved: [Peter Zijlstra, Valentin Schneider]
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "sched_domains_numa_masks 在分配失败时未释放已分配的部分掩码，存在小内存泄漏/不一致。补上分配失败路径的清理（free 已分配掩码）。同作者在 19062 讨论 topology 分配失败的其它清理。"
    review_outcome: "v1 刚发，邮件未显示 NAK。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["属低频错误路径清理，需确认与 19062 的其它清理是否合并处理"]
  next_action: "等待 maintainer 对该错误路径清理的认可。"
contribution_opportunities:
  - kind: review
    description: "可审阅在 sched domain 构建失败回滚路径中是否还有其他未释放的 per-node 分配，回帖补充（与 19062 合并讨论）。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [topology, numa, cleanup]
---
