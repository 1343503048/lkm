---
id: sched-20260903-008
date: '2026-09-03'
subject: 'sched/cputime: Account cgroup fields to the scheduling context'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/cputime+Account+cgroup+fields+to+the+scheduling+context
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Hui Su
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 4
related_articles:
- sched-20260903-001
tags:
- sched/core
- cgroup
- proxy_execution
title: 'sched/cputime: Account cgroup fields to the scheduling context'
layout: article
---

## TL;DR

代理执行分离调度上下文与执行上下文。调度器运行时间记账将 cgroup 时间记到 donor，而 tick 与 vtime 记账在更新 cgroup 字段时却使用执行任务。目前单 patch，附复现说明。- 属「代理执行执行上下文修正」主线，与同日 001/005 同源。

## 背景与问题

代理执行分离调度上下文与执行上下文。调度器运行时间记账将 cgroup 时间记到 donor，而 tick 与 vtime 记账在更新 cgroup 字段时却使用执行任务。当 donor 与执行任务分属不同 cgroup 时，会把 donor cgroup 的 `cpu.stat` usage 记给 donor，而 user/system 字段记给执行任务 cgroup，造成统计错乱（donor cgroup 凭空获得 usage 时间，执行 cgroup 获得 system 时间）。

## 技术方案

- 统一 cgroup 字段（`usage` / `user` / `system`）的记账所指向的上下文，修复分裂记账。
- 修复前复现：donor 与执行任务分处不同 cgroup 时，usage 与 system 分别落到不同 cgroup。

## 版本演进与当前进展

- 单 patch，附复现说明。
- 属「代理执行执行上下文修正」主线，与同日 001/005 同源。

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
  - [[sched-20260903-001]] 代理执行下执行上下文 tick 处理（同源主线）。
- 相关代码/commit：
  - `kernel/sched/cputime.c` cgroup 时间记账路径
