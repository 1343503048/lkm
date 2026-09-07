---
id: sched-20260904-006
date: '2026-09-04'
subject: 'sched/fair: Avoid creating misfits during cache-aware balancing'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/fair+Avoid+creating+misfits+during+cache-aware+balancing
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
- sched-20260903-011
- sched-20260903-012
tags:
- sched/fair
- sched/cache
- load_balance
title: 'sched/fair: Avoid creating misfits during cache-aware balancing'
layout: article
---

## TL;DR

提交 f0d243a96f26 "sched/fair: Avoid creating misfits during cache-aware balancing" 已进入 tip/sched/urgent，并通过 0day 58 个 config 构建（BUILD SUCCESS，elapsed ~2817m）。目前已合入 tip/sched/urgent 并构建成功（[tip:sched:urgent] BUILD SUCCESS f0d243a）。

## 背景与问题

提交 `f0d243a96f26` "sched/fair: Avoid creating misfits during cache-aware balancing" 已进入 `tip/sched/urgent`，并通过 0day 58 个 config 构建（BUILD SUCCESS，elapsed ~2817m）。该修复针对 cache-aware 负载均衡中引入 misfit 任务的问题（与 `migrate_llc_task` / `sched/cache` 辅助框架相关），避免不必要的跨域迁移抖动。

## 技术方案

- 在 cache-aware 均衡路径避免创建 misfit，减少错误的跨 LLC/NUMA 迁移。

## 版本演进与当前进展

- 已合入 `tip/sched/urgent` 并构建成功（[tip:sched:urgent] BUILD SUCCESS f0d243a）。
- 属 cache-aware 均衡主线，与 09-03 的 migrate_llc_task v4 / cache 迁移 helper RFC 协同。

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
  - [[sched-20260903-011]] migrate_llc_task 语义 v4 主动均衡。
  - [[sched-20260903-012]] sched/cache 迁移决策 helper RFC v2。
- 相关代码/commit：
  - `f0d243a96f26` "sched/fair: Avoid creating misfits during cache-aware balancing"
  - `kernel/sched/fair.c` cache-aware 均衡
