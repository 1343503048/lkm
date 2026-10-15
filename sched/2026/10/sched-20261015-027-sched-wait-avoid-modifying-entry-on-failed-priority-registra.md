# sched/wait: Avoid modifying entry on failed priority registration

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261011-002：Hui Su 修复 `add_wait_queue_priority_exclusive()` 的小正确性问题——在检查是否已存在 priority waiter 之前就设置了 `WQ_FLAG_EXCLUSIVE`/`WQ_FLAG_PRIORITY`，注册因 `-EBUSY` 失败时 entry 未入队却被改了 flags；补丁把 flags 更新移到失败检查之后。
- sched-20261012-016：Sean Christopherson 参与讨论并认可方向（后续给出 Reviewed-by）。
- sched-20261015-027（今天）：tip-bot2 确认已合并进 tip 的 **sched/core** 分支（Commit-ID `159b172906110f736fdbd7af8a21d0e0b469f671`）。

## 背景与问题
（承接 20261011-002）`add_wait_queue_priority_exclusive()` 在「检查 wait 队列头部是否已有带 `WQ_FLAG_PRIORITY` 的 waiter」这一失败检查之前，就先设置 `WQ_FLAG_EXCLUSIVE | WQ_FLAG_PRIORITY`；失败返回 `-EBUSY` 时 entry 被留下未入队但 flags 已被改。属失败路径上的副作用缺陷。

## 技术方案
（承接 20261011-002）把 `wq_entry->flags |= WQ_FLAG_EXCLUSIVE | WQ_FLAG_PRIORITY` 从锁外移到「`-EBUSY` 失败检查之后、`list_add()` 之前」。`kernel/sched/wait.c` 1 文件，+1/−2。今日合并进 tip/sched/core，Committer 为 Peter Zijlstra（Intel），带 Sean Christopherson 的 Reviewed-by。

## 版本演进与当前进展
- v1（2026-10-11，<20261011015019.4056529-1-sh_def@163.com>）→ 今日合入 tip/sched/core。

## Maintainer 意见与讨论焦点
Peter Zijlstra 已合并（Committer）；Sean Christopherson Reviewed-by。无遗留分歧。

## 合入评估
*likelihood=merged*。已进 tip/sched/core。*blocking_issues*：无。*next_action*：随 sched/core 进主线（v7.4 周期）。

## 效果评估
无量化数据，属失败路径正确性修复。

## 我可以参与的点
当前阶段暂无明显参与空间，已合入 tip。

## 参考链接
- tip-bot2 合并通知：https://lore.kernel.org/all/179205153011.2666988.8056837708928643024.tip-bot2@tip-bot2/
- 原始补丁：https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/
- tip commit：https://git.kernel.org/tip/159b172906110f736fdbd7af8a21d0e0b469f671

---
id: sched-20261015-027
date: 2026-10-15
subject: "sched/wait: Avoid modifying entry on failed priority registration"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261011015019.4056529-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261011015019.4056529-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: ["Peter Zijlstra", "Sean Christopherson"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261011015019.4056529-1-sh_def@163.com>"
    date: 2026-10-11
    summary: "flags 更新移到 -EBUSY 失败检查之后"
    review_outcome: "Sean Christopherson Reviewed-by；Peter 今日合入 tip/sched/core"
upstream_commit: "159b172906110f736fdbd7af8a21d0e0b469f671"
fixes_commit: null
merged_branch: "sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/core 进主线（v7.4 周期）"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20261011-002", "sched-20261012-016"]
tags: [wait]
---