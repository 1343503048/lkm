---
id: sched-20260905-004
date: '2026-09-05'
subject: 'sched: dynamic: Fix preemption model strings'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+dynamic+Fix+preemption+model+strings
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors: []
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 0
related_articles:
- sched-20260903-013
tags:
- preempt
- sched/core
title: 'sched: dynamic: Fix preemption model strings'
layout: article
---

## TL;DR

提交 ef9293b3b797 "sched: dynamic: Fix preemption model strings" 进入 tip/sched/core，并通过 0day 74 个 config 构建（BUILD SUCCESS）。目前已合入 tip/sched/core 并构建成功（[tip:sched:core] BUILD SUCCESS ef9293b）。

## 背景与问题

提交 `ef9293b3b797` "sched: dynamic: Fix preemption model strings" 进入 `tip/sched/core`，并通过 0day 74 个 config 构建（BUILD SUCCESS）。该修复修正 PREEMPT_DYNAMIC 下抢占模型字符串的显示/取值问题，属 PREEMPT_DYNAMIC 简化工作的后续收尾。

## 技术方案

- 修正 preemption model 字符串（与 /sys 或调试输出相关），使其与当前抢占模型一致。

## 版本演进与当前进展

- 已合入 `tip/sched/core` 并构建成功（[tip:sched:core] BUILD SUCCESS ef9293b）。
- 属 PREEMPT_DYNAMIC 主线，与 09-03 013（PREEMPT_DYNAMIC 简化 v2）协同。

## Maintainer 意见与讨论焦点

邮件清单中该系列以补丁往返为主，未捕获到维护者明确表态（缓存未含正文，无法给出具体意见）。

## 合入评估

证据不足：邮件缓存未保留正文，无法判断维护者态度与卡点，暂不给合入结论。

## 效果评估

邮件中未提及效果数据（缓存未保留正文，无法确认）。

## 我可以参与的点

证据不足：需结合完整邮件正文再判断参与空间；如该系列进入 review 中后期，可先跑一轮 benchmark 并回帖。

## 参考链接

- 相关文章/系列：
  - [[sched-20260903-013]] PREEMPT_DYNAMIC 简化 v2 0/6。
- 相关代码/commit：
  - `ef9293b3b797` "sched: dynamic: Fix preemption model strings"
  - `kernel/sched/core.c` PREEMPT_DYNAMIC
