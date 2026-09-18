# sched_ext: Derive SCX_RQ_IN_WAKEUP from the core enqueue flags

## TL;DR
增量更新：Tejun Heo 的 sched_ext 修复（从核心 enqueue flags 派生出 `SCX_RQ_IN_WAKEUP`，替代 sched_ext 自行维护的 wakeup 标记）本日被 Tejun 亲自合入 `sched_ext/for-7.3-fixes`，将随 7.3-rc 周期进入主线。

## 背景与问题
背景见 sched-20260917-011：sched_ext 在 enqueue 路径自行维护 wakeup 场景标记，与核心调度器的 enqueue flags 存在不一致/重复，需要改成从核心 flags 派生，避免状态漂移。

## 技术方案
从核心 enqueue flags 派生出 `SCX_RQ_IN_WAKEUP`，去掉 sched_ext 内部重复维护的标记位。

## 版本演进与当前进展
- 首版（09-16，`<20260916215713.2701551-1-tj@kernel.org>`）：本日被 Tejun 合入 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点
- **Tejun Heo**：直接 "Applied to sched_ext/for-7.3-fixes. Thanks."，无分歧。

## 合入评估
likelihood=merged。已合入 sched_ext 的 for-7.3-fixes 分支，等待随该分支提交进入主线。blocking_issues：无。next_action：跟踪该 Fixes 分支是否被 Linus 收纳。

## 效果评估
邮件未附性能数据；属状态维护类重构/修复，无直接性能影响。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察该修复是否随 7.3 合并窗进入主线。

## 参考链接
- lore（patch）: https://lore.kernel.org/all/20260916215713.2701551-1-tj@kernel.org/

---
id: sched-20260918-006
date: '2026-09-18'
subject: 'sched_ext: Derive SCX_RQ_IN_WAKEUP from the core enqueue flags'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260916215713.2701551-1-tj@kernel.org>'
lore_url: 'https://lore.kernel.org/all/20260916215713.2701551-1-tj@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260916215713.2701551-1-tj@kernel.org>'
    date: '2026-09-16'
    summary: '从核心 enqueue flags 派生 SCX_RQ_IN_WAKEUP'
    review_outcome: 'Tejun 本日合入 sched_ext/for-7.3-fixes'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '等待 for-7.3-fixes 分支被 Linus 收纳'
contribution_opportunities: []
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260917-011
tags:
  - sched_ext
---