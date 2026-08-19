# docs/scheduler: fix EEVDF-related inaccuracies in the scheduler docs

## TL;DR

Zhan Xusheng 修复调度器文档中两处 EEVDF 相关的不准确描述：`sched-design-CFS.rst` 仍描述 fair class 为总是运行最小 vruntime 任务（实际自 Linux 6.6 起已实现 EEVDF），`sched-eevdf.rst` 中发布日期和 `sched_setattr()` 描述有误。纯文档修复，无代码改动。

## 背景与问题

1. `sched-design-CFS.rst` 的 sections 2 和 3 仍描述原始 CFS 设计（最小 vruntime / "leftmost" task 选择），但自 commit `147f3efaa241` (Linux 6.6) 起，fair class 已实现 EEVDF —— `pick_eevdf()` 选择 eligible task (lag >= 0) 中 virtual deadline 最早的
2. `rq->cfs.min_vruntime` 字段已不存在，现在是 `cfs_rq->zero_vruntime`
3. `sched-eevdf.rst` 错误声称 Linux 6.6 发布于 2024 年（实际为 2023 年），且将 `sched_setattr()` 描述为"新的系统调用"（实际自 Linux 3.14 起已存在）

## 技术方案

- 在 `sched-design-CFS.rst` 添加 note 说明 sections 2 和 3 描述的是原始 CFS 设计，不再匹配代码
- 修复 `sched-eevdf.rst` 中的发布日期和 `sched_setattr()` 描述
- 不重写历史文本，只添加说明性 note

代码改动：`Documentation/scheduler/sched-design-CFS.rst` +10 行，`Documentation/scheduler/sched-eevdf.rst` +4/-3 行

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无。

## 合入评估

- **likelihood**: high
- 纯文档修复，改动准确且无争议

## 效果评估

暂无效果数据（纯文档改进）。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "docs/scheduler: fix EEVDF-related inaccuracies in the scheduler docs"
id: sched-20260730-006
date: 2026-07-30
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260729-sched-docs-eevdf-fix...@gmail.com>"
lore_url: "https://lore.kernel.org/lkml/20260729-sched-docs-eevdf-fix"
authors: [Zhan Xusheng]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260729-sched-docs-eevdf-fix...@gmail.com>"
    date: 2026-07-29
    summary: "Fix EEVDF-related inaccuracies in scheduler documentation"
    review_outcome: "No review feedback yet"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Wait for review"
contribution_opportunities: []
generated_at: "2026-07-31T00:10:00"
source_email_count: 1
related_articles: []
tags: [eevdf, sched_debug]
---
