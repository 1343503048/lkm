# cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()

## TL;DR
本文为增量更新，完整背景见 sched-20260921-008。Guopeng Zhang 的 v2 补丁（从 `update_prstate()` 移除冗余的调度域重建）当天获 Tejun Heo 回复「Applied to cgroup/for-7.4」——已被合入 cgroup 树，等待进入下一合入窗口。系列以 merged 收尾。

## 背景与问题
背景见 sched-20260921-008：cpuset 的 `update_prstate()` 在分区状态更新时做了冗余的调度域重建，v2 移除之。

## 技术方案
方案见 sched-20260921-008。

## 版本演进与当前进展
v2（`<20260920025256.24991-1-guopeng.zhang@linux.dev>`）后，当天 Tejun Heo 回帖合入 `cgroup/for-7.4`。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（cgroup 维护者）：「Applied to cgroup/for-7.4.」无争议，直接收取。

## 合入评估
*likelihood=merged*。已合入 `cgroup/for-7.4` 维护者树。blocking_issues 无；next_action 无（等待随 cgroup 树进入主线）。

## 效果评估
无性能数据；清理冗余操作（见 sched-20260921-008）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入维护者树）。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/
- Tejun 合入: https://lore.kernel.org/all/ffbe8ebdff9cf70efdec0eed8b37c107@kernel.org/

---
id: sched-20260922-018
date: '2026-09-22'
subject: 'cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: '<20260920025256.24991-1-guopeng.zhang@linux.dev>'
lore_url: 'https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/'
authors:
  - 'Guopeng Zhang'
maintainers_involved:
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: '2026-09-19'
    summary: '初版（见 sched-20260920-002 前的讨论）'
    review_outcome: '未获取到 v1 细节'
  - version: v2
    msgid: '<20260920025256.24991-1-guopeng.zhang@linux.dev>'
    date: '2026-09-20'
    summary: '移除 update_prstate 冗余调度域重建'
    review_outcome: 'Tejun 合入 cgroup/for-7.4'
upstream_commit: null
fixes_commit: null
merged_branch: 'cgroup/for-7.4'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '等待随 cgroup 树进入主线'
contribution_opportunities: []
generated_at: '2026-09-23T00:00:00'
source_email_count: 1
related_articles:
  - sched-20260921-008
tags:
  - cgroup
  - topology
---