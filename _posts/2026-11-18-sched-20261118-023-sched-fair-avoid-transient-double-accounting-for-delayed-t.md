---
id: sched-20261118-023
date: '2026-11-18'
subject: 'sched/fair: Avoid transient double accounting for delayed tasks'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
lore_url: https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/
authors:
- K Prateek Nayak
maintainers_involved:
- Vincent Guittot
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
  date: '2026-11-12'
  summary: 修 delayed dequeue 瞬时双记账，为非法唤醒 flag 加告警
  review_outcome: Vincent RB，合入 sched/urgent
upstream_commit: 486c3d06b90240860e99686d29ed9f15637dc314
fixes_commit: 85570f10a4c6
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 进入 7.4-rc 修复
contribution_opportunities: []
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261112-004
tags:
- cfs
- eevdf
title: 'sched/fair: Avoid transient double accounting for delayed tasks'
layout: article
---

## TL;DR

K Prateek Nayak 的 delayed-dequeue 记账修复**今日合入 tip/sched/urgent**（commit `486c3d06b902`）：delayed 任务被 delay 时 `set_delayed()` 已调整 `h_nr_runnable`，但带 `DEQUEUE_DELAYED` 的 dequeue 又在 `dequeue_hierarchy()` 里再减一次，导致早期启动可靠触发 `WARN_ON_ONCE(h_nr_runnable < 0)`，且瞬时错误值被缓存进 `se->runnable_weight` 影响 PELT。补丁在 `__dequeue_task()` 里修掉错误记账，并为「delayed 任务只带 ENQUEUE_WAKEUP 就走到 enqueue」加告警（Fixes: 85570f10a4c6）。Vincent Guittot 已 Reviewed-by。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-004-sched-fair-avoid-transient-double-accounting-for-delayed-tas.html">sched-20261112-004</a>）单 runqueue 化（`85570f10a4c6`）后，delayed 任务在 dequeue 路径存在「先多减、再纠正」的瞬时双记账，`se->runnable_weight` 会被瞬时污染并影响 PELT，直到下一次 enqueue/dequeue 才纠正。

## 技术方案

（承接）单补丁 `kernel/sched/fair.c`（+27/-34 量级）：`__dequeue_task()` 避免错误 `h_nr_runnable` 记账；为「delayed 任务带 `ENQUEUE_WAKEUP` 走到 enqueue」这一非法唤醒 flag 组合加告警。

## 版本演进与当前进展

已合入 tip/sched/urgent（`486c3d06b902`，AuthorDate 2026-11-12，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：Reviewed-by（承接 20261112-004）。
- **Peter Zijlstra**：Commiter 合入（此前「Urgh, thanks!」认可方向）。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/urgent（`486c3d06b902`）。*blocking_issues*：无。*next_action*：随 sched/urgent 进入 7.4-rc 修复。

## 效果评估

无量化数据；消除可复现的 `WARN_ON_ONCE` 与瞬时 `runnable_weight` 污染（影响 PELT）。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/486c3d06b90240860e99686d29ed9f15637dc314
- lore thread: https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/
