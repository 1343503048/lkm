---
id: sched-20261031-013
date: 2026-10-31
subject: 'sched_ext: Call ops.sub_attach() only while the cgroup is online'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20261029222859.3099324-1-tj@kernel.org>
lore_url: https://lore.kernel.org/all/20261029222859.3099324-1-tj@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Andrea Righi
- Tejun Heo
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: ebeca1f930ea
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 随 sched_ext 的 v7.4 fixes pull 合入 tip
contribution_opportunities: []
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20261030-010
tags:
- sched_ext
- cgroup
title: 'sched_ext: Call ops.sub_attach() only while the cgroup is online'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-010-sched-ext-call-ops-sub-attach-only-while-the-cgroup-is-onlin.html">sched-20261030-010</a>：Tejun Heo 修 sched_ext cgroup sub-scheduler 竞态——`ops.sub_attach()` 应在 `cgroup_lock()` 下先检查 `CSS_ONLINE`，仅对 online cgroup 调用，否则 `-ENODEV`。`Fixes: ebeca1f930ea`，当日已获 Andrea Righi Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-013-sched-ext-call-ops-sub-attach-only-while-the-cgroup-is-onlin.html">sched-20261031-013</a>（今天）：Tejun 标注 **Applied to sched_ext/for-7.4-fixes**，正式进入维护者 fixes 分支。

## 背景与问题
（承接）父调度器可能为「rmdir 已返回」的 cgroup 收到 attach 回调，与父侧清理竞争。今日无新增技术信息，为合入状态变更。

## 技术方案
（承接 20261030-010，方案不变）`scx_sub_enable_workfn()` 里 `cgroup_lock()` 下检查 `CSS_ONLINE`，非 online 则 `-ENODEV` 退出。

## 版本演进与当前进展
*current_version: v1*（2026-10-29 发出）。今日合入 `sched_ext/for-7.4-fixes`，附 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。

## Maintainer 意见与讨论焦点
Andrea Righi 已 Reviewed-by（前一版）；Tejun 今日 Applied，无遗留分歧。

## 合入评估
*likelihood=high*。已进维护者 `sched_ext/for-7.4-fixes` 分支，等待随 pull 进入 tip/主线。*blocking_issues*：暂无。*next_action*：随 sched_ext 的 v7.4 fixes pull 合入 tip。

## 效果评估
无性能数据；修复为 cgroup sub-scheduler 生命周期正确性问题。

## 我可以参与的点
当前阶段暂无明显参与空间（已进维护者分支）；可关注随 pull 进入 -rc 后的 sub-scheduler 压力回归。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261029222859.3099324-1-tj@kernel.org/
