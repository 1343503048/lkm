---
id: sched-20261106-022
date: 2026-11-06
subject: 'sched/topology: Balance cluster static-key updates'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <179395863508.1009794.5632256681899581681.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179395863508.1009794.5632256681899581681.tip-bot2@tip-bot2/
authors:
- Hui Su
maintainers_involved:
- Ingo Molnar
- Peter Zijlstra
current_version: v3
patch_series:
- version: v3
  msgid: <20261021043834.1140951-1-sh_def@163.com>
  date: 2026-10-21
  summary: detach_destroy_domains 仅当确有 SD_CLUSTER 域才递减 static key。
  review_outcome: K Prateek Nayak/Kayra 双 Reviewed-by；11-06 合入 tip/sched/urgent。
upstream_commit: 5ebdfe12ab96368d0339593129d4ce0bc2bd06f5
fixes_commit: 8881e1639f1f
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 进入主线并评估 stable 回合
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261022-009
tags:
- topology
- load_balance
title: 'sched/topology: Balance cluster static-key updates'
layout: article
---

## TL;DR

Hui Su 的修复今日合入 tip/sched/urgent（commit `5ebdfe12ab96368d0339593129d4ce0bc2bd06f5`）：`sched_cluster_active` static key 的增/减不对称——`build_sched_domains()` 每建一个含 SD_CLUSTER 域的分区就加一次，而 `detach_destroy_domains()` 删分区时只看全局 key 是否使能就减，导致销毁「不含 cluster 域」的分区会误减别的分区持有的引用、把 cluster-aware 调度全局关掉。此前已获 K Prateek Nayak 与 Kayra Cizmeci 双 Reviewed-by。

## 背景与问题

`detach_destroy_domains()` 删除分区时，只要 `sched_cluster_active` 使能就无条件递减 static key——但被删的分区可能本身不含 SD_CLUSTER 域，递减就误伤了另一分区持有的引用；结果 SD_CLUSTER 域仍在安装、cluster-aware 调度却被禁用。作者给出验证：两个带 cluster 的分区装上后移除一个 singleton 分区，基线计数停在 1（实际还有 2 个分区带 SD_CLUSTER），修复后正确报 2。

## 技术方案

`detach_destroy_domains()` 在 key 使能时先扫描被删分区的 CPU 是否安装 SD_CLUSTER 域（`lowest_flag_domain(i, SD_CLUSTER)`），仅当确有 cluster 域才递减 static key。改动 `kernel/sched/topology.c` +14/-2 行。

## 版本演进与当前进展

*current_version: v3（2026-10-22 发出）*。v1→v2 按 K Prateek Nayak 意见用 key 守卫扫描、Kayra 补 Reviewed-by；v3 按 Tim Chen 建议并入 detach 循环、递减移到 detach 后、加 Cc: stable。今日合入 tip/sched/urgent。

## Maintainer 意见与讨论焦点

K Prateek Nayak 与 Kayra Cizmeci 双 Reviewed-by；Tim Chen 确认 inc/dec 确实不平衡并建议回合 stable。无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，commit `5ebdfe12ab96368d0339593129d4ce0bc2bd06f5`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线，并按 Tim 建议评估 stable 回合。

## 效果评估

作者验证：两 cluster 分区 + 移除 singleton 分区场景下，基线计数错停在 1、修复后正确报 2；非对称 cluster 拓扑（父分区无 cluster 域）基线跌到 0、修复后保持 1。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/5ebdfe12ab96368d0339593129d4ce0bc2bd06f5
- 原补丁 lore: https://patch.msgid.link/20261021043834.1140951-1-sh_def@163.com
