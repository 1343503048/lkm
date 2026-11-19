---
id: sched-20261119-010
date: '2026-11-19'
subject: 'sched/topology: Remove stale comment around llc_bytes on powerpc'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261118163639.890546-6-sshegde@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261118163639.890546-6-sshegde@linux.ibm.com/
authors:
- Shrikanth Hegde
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261118163639.890546-6-sshegde@linux.ibm.com>
  date: '2026-11-18'
  summary: 删除 PowerPC 上 cache-aware 调度被禁用的过期注释（7 行）
  review_outcome: 当日无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 前置 arch 补丁（generic cacheinfo 迁移）需确认成立
  next_action: 随 5 补丁系列一起由维护者收取
contribution_opportunities:
- kind: review
  description: 确认 PowerPC 迁移 generic cacheinfo 后 get_effective_llc_bytes 返回非零
generated_at: '2026-11-20T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- topology
title: 'sched/topology: Remove stale comment around llc_bytes on powerpc'
layout: article
---

## TL;DR

Shrikanth Hegde（IBM）发 5 补丁系列的最后一枚 sched 侧补丁：PowerPC 现已填充 generic cacheinfo（前 4 枚多半是 arch/powerpc 侧改动，本日缓存仅在 sched 侧捕获到 patch 5/5），`get_effective_llc_bytes()` 已能在 PowerPC 上读取 LLC size，故删除 `sched_update_llc_bytes()` 上方「PowerPC 上 `get_effective_llc_bytes()` 恒返回 0、因而 cache-aware 调度在 PowerPC 上被禁用」的过期注释。纯注释清理，7 行删除，无功能变更。当日未见 review。

## 背景与问题

`kernel/sched/topology.c` 的 `sched_update_llc_bytes()` 有一段注释声称 PowerPC 不走 generic cacheinfo 框架、`get_effective_llc_bytes()` 读不到 LLC size，因此 cache-aware 调度在 PowerPC 上关闭。随着 PowerPC 迁移到 generic cacheinfo（本系列的前置 arch 补丁），该前提已不成立，注释变成误导。

## 技术方案

删除 `sched_update_llc_bytes()` 上方 7 行过期注释（含「get_effective_llc_bytes() returns 0 on PowerPC」「PowerPC does not use the generic cacheinfo framework」等），保留函数本身的正确性说明。仅文档改动，无行为变化。

## 版本演进与当前进展

*current_version: v1（2026-11-18，`<20261118163639.890546-6-sshegde@linux.ibm.com>`，系列 patch 5/5）*。当日无 review；本日缓存仅含 sched 侧 patch 5/5，其余 4 枚（推测为 powerpc arch 侧）未捕获到。

## Maintainer 意见与讨论焦点

当日未见调度维护者表态，也未见其他评审；纯注释清理、风险极低。

## 合入评估

*likelihood=high*。纯注释删除、无逻辑变更，属于顺手清理，通常直接收取。*blocking_issues*：需确认前置 arch 补丁（generic cacheinfo 迁移）是否成立。*next_action*：随所在 5 补丁系列一起由维护者收取。

## 效果评估

无性能数据；改动为注释清理，效果仅在于消除误导性说明。

## 我可以参与的点

- **review**：确认 PowerPC 迁移到 generic cacheinfo 后 `get_effective_llc_bytes()` 确实能返回非零值（注释移除的前提成立）。

## 参考链接

- lore thread（patch 5/5）: https://lore.kernel.org/all/20261118163639.890546-6-sshegde@linux.ibm.com/
