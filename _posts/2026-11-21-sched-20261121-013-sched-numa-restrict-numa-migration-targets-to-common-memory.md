---
id: sched-20261121-013
date: '2026-11-21'
subject: 'sched/numa: restrict NUMA migration targets to common memory'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261120-private_nodes_v6-v1-10-74f5f9a115c2@gourry.net>
lore_url: https://lore.kernel.org/all/20261120-private_nodes_v6-v1-10-74f5f9a115c2@gourry.net/
authors:
- Gregory Price
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261120-private_nodes_v6-v1-10-74f5f9a115c2@gourry.net>
  date: '2026-11-20'
  summary: should_numa_migrate_memory() 判定 N_MEMORY 收紧为 N_MEMORY_COMMON
  review_outcome: 无 review 信息
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无本系列 review 信息
  next_action: 随 private nodes 系列整体评审推进
contribution_opportunities:
- kind: review
  description: 核对 N_MEMORY_COMMON 与 N_MEMORY 差异覆盖无 __GFP_THISNODE zonelist 的节点
generated_at: '2026-11-22T01:00:00+08:00'
source_email_count: 91
related_articles: []
tags:
- numa_balancing
title: 'sched/numa: restrict NUMA migration targets to common memory'
layout: article
---

## TL;DR

Gregory Price（Meta）的「private nodes v6」60 补丁大系列之 10/60：把 `should_numa_migrate_memory()` 迁移目标判定从 `N_MEMORY` 收紧为 `N_MEMORY_COMMON`，避免把 folio 迁到「有 CPU 但 `__GFP_THISNODE` zonelist 为空」的节点。单行 sched/numa 改动，当日仅该补丁命中调度关键词，未见本系列其它补丁与讨论。

## 背景与问题

`should_numa_migrate_memory()` 已拒绝向 memoryless 节点迁移 folio（commit 3fb43636876d，「sched/numa, mm: do not try to migrate memory to memoryless nodes」）。但 `N_MEMORY_COMMON` 之外的节点可以有 CPU 却具有空的 `__GFP_THISNODE` zonelist：来自其 CPU 的 NUMA hinting fault 会把 folio 隔离、目标分配失败后又放回，做无用功。

## 技术方案

把判定 `!node_state(dst_nid, N_MEMORY)` 改为 `!node_state(dst_nid, N_MEMORY_COMMON)`（`kernel/sched/fair.c`，1 行），使其与「memoryless 不迁移」的既有语义落在同一张图上。

## 版本演进与当前进展

*current_version: v1（2026-11-20 发出，`<20261120-private_nodes_v6-v1-10-74f5f9a115c2@gourry.net>`，60 补丁系列之 10）*。当日无 review；属大系列中调度相关的一个切片。

## Maintainer 意见与讨论焦点

当日缓存未见对本补丁或本系列的 review/维护者表态；无 NAK 信息。

## 合入评估

*likelihood=unknown*。单行语义收紧、风险低，但作为 60 补丁大系列之一，合入路径跟随整系列节奏，本日缓存无 review 可见，不足以判断。*blocking_issues*：无本系列 review 信息。*next_action*：随 private nodes 系列整体评审推进。

## 效果评估

无性能数据；价值在避免「迁到无 common memory 的节点」导致的无效迁移与 folio 隔离。

## 我可以参与的点

- **review**：核对 `N_MEMORY_COMMON` 与 `N_MEMORY` 在 NUMA hinting fault 路径上的差异是否完全覆盖「有 CPU 但无 __GFP_THISNODE zonelist」的节点类型。

## 参考链接

- lore thread（10/60）: https://lore.kernel.org/all/20261120-private_nodes_v6-v1-10-74f5f9a115c2@gourry.net/
