---
id: sched-20260903-011
date: '2026-09-03'
subject: 'sched/cache: Honor migrate_llc_task semantics in active load balance'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/cache+Honor+migrate_llc_task+semantics+in+active+load+balance
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v4
generated_at: null
authors:
- Lu Wang
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 1
related_articles:
- sched-20260902-009
tags:
- sched/cache
- load_balance
- affinity
title: 'sched/cache: Honor migrate_llc_task semantics in active load balance'
layout: article
---

## TL;DR

migrate_llc_task 语义用于表达「任务应优先在所属 LLC 域内迁移」。目前v4，复审中；与 sched-20260902-009 的 NUMA 细粒度 + sched/cache 辅助框架协同演进。

## 背景与问题

`migrate_llc_task` 语义用于表达「任务应优先在所属 LLC 域内迁移」。本系列在主动负载均衡（active load balance）路径中尊重该语义，避免把本应限制在 LLC 内的任务错误地推到跨 LLC 的 CPU，减少跨域缓存/内存带宽代价。

## 技术方案

- 主动负载均衡在选择迁移目标时，参考 `migrate_llc_task` 标记，约束候选 CPU 范围到所属 LLC 域。

## 版本演进与当前进展

- v4，复审中；与 `sched-20260902-009` 的 NUMA 细粒度 + `sched/cache` 辅助框架协同演进。

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
  - [[sched-20260902-009]] NUMA 细粒度 + sched/cache 辅助（RFC v2）。
- 相关代码/commit：
  - `kernel/sched/fair.c` `active_load_balance()` / `migrate_llc_task`
