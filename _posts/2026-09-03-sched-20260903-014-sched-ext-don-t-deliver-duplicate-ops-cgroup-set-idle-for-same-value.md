---
id: sched-20260903-014
date: '2026-09-03'
subject: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+don%27t+deliver+duplicate+ops.cgroup_set_idle
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
- sched_ext
- cgroup
title: 'sched_ext: don''t deliver duplicate ops.cgroup_set_idle() for same value'
layout: article
---

## TL;DR

ops.cgroup_set_idle() 用于按 cgroup 设置 idle 偏好。目前本日收到复审（Re）；属 scx 操作幂等性/性能小优化。

## 背景与问题

`ops.cgroup_set_idle()` 用于按 cgroup 设置 idle 偏好。当下发的新值与当前已生效值相同时，无需重复下发该 ops 调用。本系列使之幂等，避免冗余的 BPF 回调与状态切换开销。

## 技术方案

- 在 scx 调度器侧缓存 cgroup idle 的当前取值，仅在值发生变化时才下发 `ops.cgroup_set_idle()`。

## 版本演进与当前进展

- 本日收到复审（Re）；属 scx 操作幂等性/性能小优化。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关代码/commit：
  - `kernel/sched/ext.c` cgroup idle 操作路径
