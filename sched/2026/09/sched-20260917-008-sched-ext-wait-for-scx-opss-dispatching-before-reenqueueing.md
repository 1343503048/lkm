# sched_ext: Wait for SCX_OPSS_DISPATCHING before reenqueueing a task

## TL;DR
增量更新：Tejun Heo 的 sched_ext/for-7.3-fixes 补丁"在重新入队任务前等待 SCX_OPSS_DISPATCHING"已被 Tejun 本人应用到 sched_ext/for-7.3-fixes 分支，进入 tip。该修复解决 DISPATCHING 窗口内 reenqueue 导致的竞态，至此合入。

## 背景与问题
背景见 sched-20260916-005：任务在 SCX_OPSS_DISPATCHING 窗口内被重新入队时存在竞态，需等待该状态清除后再入队，否则状态机可能错乱。

## 技术方案
无方案变化；本日仅确认合入动作。

## 版本演进与当前进展
- v1（09-16，`<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>`）：原始修复。
- 09-17：Tejun Heo 回复"Applied to sched_ext/for-7.3-fixes."，补丁进入 tip 的 sched_ext/for-7.3-fixes 分支。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（维护者+作者）：直接应用该补丁，无异议。此前 Andrea Righi 已参与评审（见 sched-20260916-005）。

## 合入评估
likelihood=merged。已进入 sched_ext/for-7.3-fixes 分支（tip）。blocking_issues：无。next_action：等待随 sched_ext fixes PR 进入 mainline v7.3-rc。

## 效果评估
无性能数据；属正确性/竞态修复。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察后续版本。

## 参考链接
- lore（v1）: https://lore.kernel.org/all/a4304b3f0c89fba23f1e5e92997a8f56@kernel.org/
- 应用确认: https://lore.kernel.org/all/9d43c95a17de1e53db7afd307713007f@kernel.org/

---
id: sched-20260917-008
date: '2026-09-17'
subject: 'sched_ext: Wait for SCX_OPSS_DISPATCHING before reenqueueing a task'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>'
lore_url: 'https://lore.kernel.org/all/a4304b3f0c89fba23f1e5e92997a8f56@kernel.org/'
authors:
  - 'Tejun Heo'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<a4304b3f0c89fba23f1e5e92997a8f56@kernel.org>'
    date: '2026-09-16'
    summary: '重新入队前等待 SCX_OPSS_DISPATCHING 清除'
    review_outcome: '已应用到 sched_ext/for-7.3-fixes'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '等待随 sched_ext fixes PR 进入 mainline'
contribution_opportunities: []
generated_at: '2026-09-18T09:00:00'
source_email_count: 1
related_articles:
  - sched-20260916-005
tags:
  - sched_ext
---