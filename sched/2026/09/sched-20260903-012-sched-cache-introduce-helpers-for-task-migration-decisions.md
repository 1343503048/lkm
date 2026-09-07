# sched/cache: Introduce helpers for task migration decisions

## TL;DR

作为 NUMA 细粒度均衡 + sched/cache 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。目前RFC v2 阶段，整体框架仍在讨论，尚未进入合入。- 与 sched-20260902-009 同一框架。

## 背景与问题

作为 NUMA 细粒度均衡 + `sched/cache` 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。

## 技术方案

- 新增任务迁移决策 helper，统一 cache/NUMA 域的迁移判据。
- 本日收到 RFC v2 11/23 的复审（Re）。

## 版本演进与当前进展

- RFC v2 阶段，整体框架仍在讨论，尚未进入合入。
- 与 `sched-20260902-009` 同一框架；与 `sched-20260903-011`（migrate_llc_task v4）互补。

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
  - [[sched-20260903-011]] migrate_llc_task v4。
- 相关代码/commit：
  - `kernel/sched/fair.c` 迁移决策 helper

---
id: sched-20260903-012
date: '2026-09-03'
subject: 'sched/cache: Introduce helpers for task migration decisions'
subsystem: sched
type: discussion
status: rfc
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/?q=sched/cache+Introduce+helpers+for+task+migration+decisions
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v2
generated_at: null
authors:
- Jianyong Wu
- Tim Chen
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: null
contribution_opportunities: []
source_email_count: 2
related_articles:
- sched-20260902-009
tags:
- sched/cache
- load_balance
- numa_balancing
---
