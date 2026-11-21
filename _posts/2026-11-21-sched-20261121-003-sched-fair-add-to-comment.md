---
id: sched-20261121-003
date: '2026-11-21'
subject: 'sched/fair: add '')'' to comment'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261121114129.1443346-2-manuelebnerli@mailbox.org>
lore_url: https://lore.kernel.org/all/20261121114129.1443346-2-manuelebnerli@mailbox.org/
authors:
- Manuel Ebner
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261121114129.1443346-2-manuelebnerli@mailbox.org>
  date: '2026-11-21'
  summary: 补全缩放公式注释缺失的右括号
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 由 sched 维护者直接收取
contribution_opportunities: []
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles: []
tags:
- cfs
title: 'sched/fair: add '')'' to comment'
layout: article
---

## TL;DR

Manuel Ebner 发一行注释修复，给 `SCHED_TUNABLESCALING_LOG` 默认值公式注释补上漏掉的右括号。

## 背景与问题

`kernel/sched/fair.c` 头部关于 sysctl 缩放模式的注释里，`(default SCHED_TUNABLESCALING_LOG = *(1+ilog(ncpus))` 漏了一个右括号，纯注释拼写错误，不影响运行行为。

## 技术方案

单行 diff：把 `(default SCHED_TUNABLESCALING_LOG = *(1+ilog(ncpus))` 改为 `(default SCHED_TUNABLESCALING_LOG = *(1+ilog(ncpus)))`，补全公式括号。

## 版本演进与当前进展

*current_version: v1（2026-11-21，`<20261121114129.1443346-2-manuelebnerli@mailbox.org>`，单补丁）*。首版，当日无 review 意见。

## Maintainer 意见与讨论焦点

暂无维护者/社区回复；属纯文档级 trivial 修复，通常无争议。

## 合入评估

*likelihood=high*。一行注释拼写修复，无逻辑改动，可由维护者在 pick 时顺手收取。*blocking_issues*：无。*next_action*：由 sched 维护者直接收取。

## 效果评估

无功能影响，无效果数据。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察后续版本。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261121114129.1443346-2-manuelebnerli@mailbox.org/
