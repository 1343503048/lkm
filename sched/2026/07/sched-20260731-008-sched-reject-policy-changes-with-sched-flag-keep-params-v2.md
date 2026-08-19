# sched: Reject policy changes with SCHED_FLAG_KEEP_PARAMS

## TL;DR

本文为增量更新，完整背景见 sched-20260730-001。Andrea Righi (NVIDIA) 的 SCHED_FLAG_KEEP_PARAMS 策略变更副作用修复 v2 在 20260731 收到 Bharata B Rao (AMD) 的确认回复。Bharata 确认修复方向正确。合入可能性高。

## 背景与问题

（完整背景见 sched-20260730-001）`SCHED_FLAG_KEEP_PARAMS` 标志旨在保持调度参数不变，但策略变更（如从 SCHED_OTHER 切换到 SCHED_FIFO）仍会产生副作用，修改了本应保持不变的参数。

## 新增讨论（20260731）

**Bharata B Rao (AMD)** 回复确认修复方向正确，无新的异议。

## 合入评估

- **likelihood: high** — 修复方向得到认可，无争议
- **blocking_issues**: 无
- **next_action**: 等待更多 review 或 maintainer 合入

## 效果评估

暂无效果数据。修复正确性问题。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260730135858.2460751-1-arighi@nvidia.com
- 前日分析: sched-20260730-001

---
subject: "sched: Reject policy changes with SCHED_FLAG_KEEP_PARAMS"
id: sched-20260731-008
date: 2026-07-31
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260730135858.2460751-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/lkml/20260730135858.2460751-1-arighi@nvidia.com"
authors: [Andrea Righi]
maintainers_involved: [Bharata B Rao]
current_version: v2
patch_series:
  - version: v2
    msgid: "<20260730135858.2460751-1-arighi@nvidia.com>"
    date: 2026-07-30
    summary: "修复 SCHED_FLAG_KEEP_PARAMS 下的策略变更副作用问题"
    review_outcome: "Bharata 确认修复方向正确"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等待更多 review 或合入"
contribution_opportunities: []
generated_at: "2026-07-31T16:30:00"
source_email_count: 2
related_articles: [sched-20260730-001]
tags: [cfs]
---
