---
id: sched-20261105-016
date: 2026-11-05
subject: 'sched/isolation: Drain per-CPU LRU batches when CPUs become isolated'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <20261103075940.110308-1-matthew.ruffell@canonical.com>
lore_url: https://lore.kernel.org/all/auvQGQs-2DXQ2Brf@WindFlash/
authors:
- Matthew Ruffell
- Caron Wills
maintainers_involved:
- Leonardo Bras
current_version: v1
patch_series:
- version: v1
  msgid: <20261103075940.110308-5-matthew.ruffell@canonical.com>
  date: 2026-11-03
  summary: patch 4/6：隔离 CPU 清空 per-CPU LRU batch。
  review_outcome: Leonardo 接手，预计月底前测试。
upstream_commit: null
fixes_commit: 1c3329df409b
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 修复未完成、尚未测试
  next_action: 等 Leonardo 月底前给出经测试的修复系列
contribution_opportunities:
- kind: testing
  description: 在 isolcpus + SCHED_FIFO 场景帮 Leonardo 验证 LRU drain 修复
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261103-002
tags:
- nohz
- affinity
- load_balance
title: 'sched/isolation: Drain per-CPU LRU batches when CPUs become isolated'
layout: article
---

## TL;DR

- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-002-mm-sched-cgroup-lru-cache-never-drains-when-isolcpus-are-use.html">sched-20261103-002</a>：Canonical 报告 isolcpus + SCHED_FIFO 忙循环导致 systemd 卡 D 状态的生产 bug，根因含 `cpu_is_isolated()` 对 nohz_full 判定退化；6 补丁系列的 patch 4/6 即本主题「隔离 CPU 清空 per-CPU LRU batch」。
- sched-20261105（今天）：sched/isolation 维护者 Leonardo Bras 就 patch 4/6 回应「Yeah, working on that. Hopefully should be tested by the end of this month」——确认该修复由他本人接手推进，预计月底前完成测试。

## 背景与问题

- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-002-mm-sched-cgroup-lru-cache-never-drains-when-isolcpus-are-use.html">sched-20261103-002</a>：192 CPU（AMD EPYC 9R45）`isolcpus=nohz` 大段隔离 + 100% SCHED_FIFO 忙循环下，50GB 跨 NUMA 页面迁移时 systemd 卡 D 状态 3-10 分钟；nohz_full CPU 的 per-CPU work 永不执行、`flush_work()` 挂起。patch 4/6 让运行时被隔离（cpuset 分区）的 CPU 在 `housekeeping_update()` 后调用 `lru_add_drain_all()` 以空 batch 起步。

今天的新进展：维护者 Leonardo Bras（sched/isolation）确认正在接手该 LRU drain 修复，并给出时间预期（月底前测试完成）。这延续了 11-03 讨论中 Frederic Weisbecker 指向 Leonardo 既有系列（lore 20260519012754）的线索。

## 技术方案

- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-002-mm-sched-cgroup-lru-cache-never-drains-when-isolcpus-are-use.html">sched-20261103-002</a>：patch 1 修 `cpu_is_isolated()` 判定退化（补测 HK_TYPE_KERNEL_NOISE）；patch 4 在 `housekeeping_update()` 更新 HK_TYPE_DOMAIN 后调用 `lru_add_drain_all()`。
- 今天：无新代码；仅维护者确认推进与时间点。

## 版本演进与当前进展

*current_version: 无新版本*。今日为维护者接手声明（Leonardo Bras「working on that，月底前测试」），方案仍落在 11-03 讨论的两条路线之一（Leonardo 系列 vs Canonical 逐个 work 队列修补）上。

## Maintainer 意见与讨论焦点

Leonardo Bras（sched/isolation 维护者）今日明确接手该 LRU drain 修复，是对 11-03 争议（Michal 提议底层 pcp flush、Tejun 质疑细粒度隔离）中「由 Leonardo 系列落地」这一方向的具体推进信号。其余分歧（底层 pcp flush vs per-work 修补）未在今日解决。

## 合入评估

*likelihood=unknown*。有维护者接手与时间预期，但修复尚未成型、方案路线（Leonardo 系列 vs 其它）仍在收敛。*blocking_issues*：修复未完成、尚未测试。*next_action*：等 Leonardo 月底前给出经测试的 v5 系列。

## 效果评估

- <a class="article-ref" href="/lkm/2026/11/03/sched-20261103-002-mm-sched-cgroup-lru-cache-never-drains-when-isolcpus-are-use.html">sched-20261103-002</a>：报告附生产可复现数据（systemd 卡 3-5 分钟、生产最长 10 分钟）。今日无新增数据。

## 我可以参与的点

- testing：在 isolcpus + SCHED_FIFO 场景复现 LRU 不 drain 问题，帮 Leonardo 验证其修复（尤其 cpuset 分区动态隔离路径）。
- discussion：参与「底层 pcp flush vs 逐个 work 队列修补」的方案取舍。

## 参考链接

- lore thread（Canonical 系列 cover）: https://lore.kernel.org/all/20261103075940.110308-1-matthew.ruffell@canonical.com/
- Leonardo 接手回帖: https://lore.kernel.org/all/auvQGQs-2DXQ2Brf@WindFlash/
