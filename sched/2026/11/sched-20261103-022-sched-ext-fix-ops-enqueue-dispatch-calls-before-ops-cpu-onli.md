# sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261101-003：修 runtime CPU up 时 sched 域重建令 rq 提前 online、导致 `ops.cpu_online()` 之前调用 `ops.enqueue()/dispatch()`；方案移除 rq_online/rq_offline 钩子、改在 `handle_hotplug()` 统一管 SCX_RQ_ONLINE（两补丁，for-7.4-fixes，Cc stable v6.12+）。
- sched-20261102-017：Andrea Righi 回帖双补丁 Reviewed-by。
- sched-20261103-022（今天）：Tejun Heo 已把补丁 1-2 收进 sched_ext/for-7.4-fixes，补记 Reviewed-by: Andrea Righi——系列合入 scx 分支。

## 背景与问题

（承接 sched-20261101-003 / 20261102-017）`ops.cpu_online()` 的文档承诺与 SCX_RQ_ONLINE 门控被 sched 域重建顺序破坏，导致 online 之前触发 `ops.enqueue()/dispatch()`。今日无新代码。

## 技术方案

（承接）`handle_hotplug()` 单独跟踪 SCX_RQ_ONLINE，放在 `ops.cpu_online()` 之后置位；sched 域重建不再触碰该标志。今日为收取确认。

## 版本演进与当前进展

*current_version: 两补丁系列（已合入）*。今日 Tejun 回 Applied：「Applied 1-2 to sched_ext/for-7.4-fixes with Reviewed-by: Andrea Righi」。

## Maintainer 意见与讨论焦点

无分歧：Andrea Righi 已 Reviewed，Tejun（sched_ext 维护者）当日收取。

## 合入评估

*likelihood=merged*。已进 sched_ext/for-7.4-fixes（Cc stable v6.12+，预期后续随 scx 树进 tip 并回合 stable）。

## 效果评估

无性能数据；属 sched_ext CPU online 时序正确性修复。

## 我可以参与的点

当前阶段暂无明显参与空间；可关注其后续进 tip 与 stable 回合（v6.12+）的进展。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261031170541.710939-1-tj@kernel.org/

---
id: sched-20261103-022
date: 2026-11-03
subject: "sched_ext: Fix ops.enqueue/dispatch() calls before ops.cpu_online()"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261031170541.710939-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261031170541.710939-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: [Tejun Heo, Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261031170541.710939-1-tj@kernel.org>"
    date: 2026-10-31
    summary: "两补丁：移除 rq_online/rq_offline 钩子，handle_hotplug 统一管 SCX_RQ_ONLINE。"
    review_outcome: "Andrea Righi Reviewed；Tejun 已收进 sched_ext/for-7.4-fixes。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已合入 scx 分支，关注进 tip 与 stable 回合。"
contribution_opportunities: []
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261102-017]
tags: [sched_ext]
---