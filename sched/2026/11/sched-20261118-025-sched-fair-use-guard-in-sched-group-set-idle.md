# sched/fair: Use guard in sched_group_set_idle()

## TL;DR

Peter Zijlstra 的清理补丁**今日合入 tip/sched/urgent**（commit `9a92f776dfa6`）：`sched_group_set_idle()` 改用 `guard` 管理 `rq_lock_irqsave()`，配合「`cfs_rq::idle` 改为祖先 tg::idle 之和」（sched-20261118-022）的语义变化做针对性清理。属同名配套的轻量整理，无行为变化。

## 背景与问题

`sched_group_set_idle()` 在「`cfs_rq::idle` 改为祖先 tg::idle 之和」语义落地后，其锁与更新逻辑可用 `guard`（scope-based 资源管理）更简洁地表达，消除显式 `struct rq_flags` 与手动 unlock。

## 技术方案

`sched_group_set_idle()` 用 `guard(rq_lock_irqsave)(rq)` 包裹更新，移除显式 rq_flags 局部变量与手动 unlock 路径。属 `sched/fair.c` 的机械清理。

## 版本演进与当前进展

已合入 tip/sched/urgent（`9a92f776dfa6`，AuthorDate 2026-11-05，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（作者/维护者）**：作为 Author+Committer 合入。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/urgent（`9a92f776dfa6`）。*blocking_issues*：无。*next_action*：随 sched/urgent 进入 7.4-rc 修复。

## 效果评估

无数据；纯清理，生成代码语义不变。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/9a92f776dfa6a88fc16fe0512c725734190bf9d0
- lore thread: https://lore.kernel.org/all/20261105170157.453569788@infradead.org/

---
id: sched-20261118-025
date: '2026-11-18'
subject: "sched/fair: Use guard in sched_group_set_idle()"
subsystem: sched
type: fix
status: merged_tip
severity: none
thread_root_msgid: "<20261105170157.453569788@infradead.org>"
lore_url: "https://lore.kernel.org/all/20261105170157.453569788@infradead.org/"
authors: [Peter Zijlstra]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series: []
upstream_commit: "9a92f776dfa6a88fc16fe0512c725734190bf9d0"
fixes_commit: null
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/urgent 进入 7.4-rc 修复"
contribution_opportunities: []
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261112-018]
tags: [cfs, cgroup]
---
