---
id: sched-20260903-013
date: '2026-09-03'
subject: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched+dynamic+Simplify+PREEMPT_DYNAMIC+v2
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Mark Rutland
- Mete Durlu
- Shrikanth Hegde
- Jinjie Ruan
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 5
related_articles:
- sched-20260902-002
tags:
- preempt
- sched/core
title: 'sched: dynamic: Simplify PREEMPT_DYNAMIC'
layout: article
---

## TL;DR

在 09-02 已合入的 PREEMPT_DYNAMIC 简化基础上，本系列（v2，0/6）进一步清理与精简 PREEMPT_DYNAMIC 的实现与静态分支选择逻辑，降低维护成本并移除遗留分支。目前v2 复审中；与 sched-20260902-002（PREEMPT_DYNAMIC 简化 + static key 迁移，已合入）同源演进。

## 背景与问题

在 09-02 已合入的 PREEMPT_DYNAMIC 简化基础上，本系列（v2，0/6）进一步清理与精简 PREEMPT_DYNAMIC 的实现与静态分支选择逻辑，降低维护成本并移除遗留分支。

## 技术方案

- 6 个 patch 的精简集，覆盖 PREEMPT_DYNAMIC 的静态分支封装与调用点整理。

## 版本演进与当前进展

- v2 复审中；与 `sched-20260902-002`（PREEMPT_DYNAMIC 简化 + static key 迁移，已合入）同源演进。

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
  - [[sched-20260902-002]] PREEMPT_DYNAMIC 简化 + static key 迁移（合入）。
  - [[sched-20260903-007]] 最后一批 deprecated static key 转换（v2）。
- 相关代码/commit：
  - `kernel/sched/core.c` PREEMPT_DYNAMIC 静态分支
