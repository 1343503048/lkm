## TL;DR

PeterZ 修复 `futex_pivot_pending()` 中的 `might_sleep()` 告警，已合入 `tip: locking/urgent` 分支。commit `d8aa5dd97944`。

## 背景与问题

`futex_pivot_pending()` 在可能睡眠的上下文中触发了 `might_sleep()` 告警。这是 futex 子系统在 pivot 操作中的路径问题。

## 技术方案

修复 `futex_pivot_pending()` 中的上下文检查，确保在允许睡眠的上下文中正确调用。

## 版本演进与当前进展

已合入 `tip: locking/urgent`，commit `d8aa5dd97944a72d4a9e3cc79bb80fcac7d6e829`。

## Maintainer 意见与讨论焦点

已合入，无争议。标记为 urgent 分支。

## 合入评估

- **likelihood**: merged
- 已合入 `tip: locking/urgent`

## 效果评估

修复告警，无性能数据。

## 我可以参与的点

当前阶段暂无明显参与空间，补丁已合入。

## 参考链接

- tip commit: https://git.kernel.org/tip/d8aa5dd97944a72d4a9e3cc79bb80fcac7d6e829
- lore thread: https://lore.kernel.org/lkml/20260820074927.GH1246887@noisy.programming.kicks-ass.net/
- stable backport: 未获取到

---
id: sched-20260821-009
date: 2026-08-21
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20260820074927.GH1246887@noisy.programming.kicks-ass.net>"
lore_url: "https://lore.kernel.org/lkml/20260820074927.GH1246887@noisy.programming.kicks-ass.net/"
authors: ["Peter Zijlstra"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260820074927.GH1246887@noisy.programming.kicks-ass.net>"
    date: 2026-08-20
    summary: "修复 futex_pivot_pending() might_sleep() 告警"
    review_outcome: "已合入 tip: locking/urgent"
upstream_commit: "d8aa5dd97944a72d4a9e3cc79bb80fcac7d6e829"
fixes_commit: null
merged_branch: "tip/locking/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入"
contribution_opportunities: []
generated_at: "2026-08-21T10:00:00"
source_email_count: 1
related_articles: []
tags: ["futex", "locking"]
---
