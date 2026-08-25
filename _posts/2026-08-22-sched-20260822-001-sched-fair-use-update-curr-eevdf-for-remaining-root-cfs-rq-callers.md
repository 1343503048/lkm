---
id: sched-20260822-001
date: 2026-08-22
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260822105930.2352761-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/lkml/20260822105930.2352761-1-zhanxusheng1024@gmail.com/
authors:
- Zhan Xusheng
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260822105930.2352761-1-zhanxusheng1024@gmail.com>
  date: 2026-08-22
  summary: 统一 root cfs_rq 调用者使用 update_curr_eevdf()
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 review
contribution_opportunities:
- kind: review
  description: 审查代码变更确认所有路径已覆盖
generated_at: '2026-08-22T10:00:00'
source_email_count: 1
related_articles: []
tags:
- sched/fair
- eevdf
title: Zhan Xusheng 提出将 `update_curr_eevdf()` 统一应用于剩余的 root cfs_rq 调用路径
layout: article
---

## TL;DR

Zhan Xusheng 提出将 `update_curr_eevdf()` 统一应用于剩余的 root cfs_rq 调用路径，确保 EEVDF 时间更新在所有路径上一致。v1 刚发出。

## 背景与问题

EEVDF 调度器使用 `update_curr_eevdf()` 更新虚拟运行时间和deadline。目前部分 root cfs_rq 的调用路径仍使用旧的更新方式，导致 EEVDF 时间更新不一致。

## 技术方案

将剩余的 root cfs_rq 调用者统一切换到 `update_curr_eevdf()`，确保所有路径使用相同的 EEVDF 更新逻辑。

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无 review 意见。

## 合入评估

- **likelihood**: medium
- **blocking_issues**: 需要确认是否有性能影响
- **next_action**: 等待 review

## 效果评估

暂无效果数据。

## 我可以参与的点

- 审查代码变更，确认所有 root cfs_rq 路径都已覆盖
- 在 EEVDF 场景下测试性能影响

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260822105930.2352761-1-zhanxusheng1024@gmail.com/
- tip-bot commit: 未获取到
- stable backport: 未获取到
