# cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()

## TL;DR
增量更新：Guopeng Zhang 的 cpuset `update_prstate()` 冗余调度域重建删除补丁（v2）昨日获 cpuset 维护者 Waiman Long 的 Reviewed-by，评审背书到位，合入概率高。

## 背景与问题
背景见 sched-20260920-002：`update_prstate()` 在 cpuset 分区状态切换时会不必要地触发一次 `rebuild_sched_domains_locked()`，与调用链上其他路径的调度域重建重复，属于冗余开销。

## 技术方案
本日无新代码。修复为从 `update_prstate()` 中删除这次冗余的调度域（sched domain）重建，依赖调用方的既有重建路径，属无功能逻辑变化的清理/修复。

## 版本演进与当前进展
- v2（09-20，thread root `<20260920025256.24991-1-guopeng.zhang@linux.dev>`）。
- 09-21：cpuset 维护者 Waiman Long 给出 `Reviewed-by`。

## Maintainer 意见与讨论焦点
- **Waiman Long（cpuset 维护者）**：给出 Reviewed-by，认可该冗余重建确可删除，无异议。

## 合入评估
likelihood=high。cpuset 维护者已明确 Review 通过，冗余重建的删除逻辑清晰、风险低。next_action：等待 cpuset/cgroup 维护者（Tejun Heo / Waiman Long）合入。

## 效果评估
无性能数据；收益定性为消除每次分区状态切换时的多余 sched domain 重建，属轻微但确定的 CPU 与锁开销节省。

## 我可以参与的点
当前阶段暂无明显参与空间（维护者已 Review 通过），可持续观察是否随 cgroup 树合入。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/

---
id: sched-20260921-008
date: '2026-09-21'
subject: 'cgroup/cpuset: Remove redundant sched domain rebuild from update_prstate()'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20260920025256.24991-1-guopeng.zhang@linux.dev>'
lore_url: 'https://lore.kernel.org/all/20260920025256.24991-1-guopeng.zhang@linux.dev/'
authors:
  - 'Guopeng Zhang'
maintainers_involved:
  - 'Waiman Long'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260920025256.24991-1-guopeng.zhang@linux.dev>'
    date: '2026-09-20'
    summary: '从 update_prstate() 删除冗余的 sched domain 重建'
    review_outcome: 'Waiman Long Reviewed-by'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: '等待 cpuset/cgroup 维护者合入'
contribution_opportunities: []
generated_at: '2026-09-22T01:10:00'
source_email_count: 1
related_articles:
  - sched-20260920-002
tags:
  - cgroup
  - topology
---