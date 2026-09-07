---
id: sched-20260903-004
date: '2026-09-03'
subject: 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched_ext+Fix+NULL+sched+deref+sub-sched+error+paths
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v3
generated_at: null
authors:
- Wanwu Li
- Tejun Heo
- Andrea Righi
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 6
related_articles:
- sched-20260902-006
tags:
- sched_ext
- crash
title: 'sched_ext: Fix NULL sched deref in kfunc sub-sched error paths'
layout: article
---

## TL;DR

在 sub-sched（子调度）的错误处理路径（open/enable 失败回滚）中，访问了已释放/未初始化的 sched 对象，导致 NULL 解引用，可能触发 NULL deref crash。目前v3 吸收评审意见，增加 stable Cc。

## 背景与问题

在 sub-sched（子调度）的错误处理路径（open/enable 失败回滚）中，访问了已释放/未初始化的 `sched` 对象，导致 NULL 解引用，可能触发 NULL deref crash。本系列覆盖两类触发点：`kfunc` 子调度错误路径与 `select_cpu_and` 子调度错误路径。

## 技术方案

- `sched_ext`：Fix NULL sched deref in kfunc sub-sched error paths（v3，作者 Wanwu Li，`Fixes: a5fa0708cbfd`，`Cc: stable`）。
- `sched_ext`：Fix NULL sched deref in `select_cpu_and` sub-sched error path（Re 复审）。

## 版本演进与当前进展

- v3 吸收评审意见，增加 `stable` Cc。
- 与 `sched-20260902-006` 的 `select_cpu_and` NULL deref 同源，本日将两类错误路径统一修复。

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
  - [[sched-20260902-006]] sched_ext select_cpu_and NULL deref（待审初版）。
- 相关代码/commit：
  - `kernel/sched/ext.c` sub-sched 错误回滚路径（`Fixes: a5fa0708cbfd`）
