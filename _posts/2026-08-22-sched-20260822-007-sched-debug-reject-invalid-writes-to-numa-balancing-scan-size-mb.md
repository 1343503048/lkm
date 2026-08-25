---
id: sched-20260822-007
date: 2026-08-22
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: 未获取到
lore_url: 未获取到
authors:
- Lirongqing
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20260822023313.1721-1-lirongqing@baidu.com>
  date: 2026-08-22
  summary: v2 拒绝无效 scan_size_mb 写入，改用 debugfs_create_file_unsafe
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 review
contribution_opportunities: []
generated_at: '2026-08-22T10:00:00'
source_email_count: 1
related_articles: []
tags:
- sched/debug
- numa
title: 'sched/debug: Reject invalid writes to numa_balancing scan_size_mb'
layout: article
---

## TL;DR

Lirongqing 的 v2 补丁为 `sched/debug` 增加对 `numa_balancing scan_size_mb` 无效写入的拒绝。v2 改用 `debugfs_create_file_unsafe` 并重写了 commit message。

## 背景与问题

`/proc/sys/kernel/numa_balancing` 的 `scan_size_mb` 参数允许无效值写入，可能导致意外行为。需要在 debugfs 层面增加输入验证。

## 技术方案

v2 改用 `debugfs_create_file_unsafe` 替代 `debugfs_create_file`，增加写入值的有效性检查。

## 版本演进与当前进展

- **v2** (resend): 改用 `debugfs_create_file_unsafe`，重写 commit message

## Maintainer 意见与讨论焦点

暂无 review 意见。

## 合入评估

- **likelihood**: medium
- **blocking_issues**: 无
- **next_action**: 等待 review

## 效果评估

增强输入验证，无性能数据。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
