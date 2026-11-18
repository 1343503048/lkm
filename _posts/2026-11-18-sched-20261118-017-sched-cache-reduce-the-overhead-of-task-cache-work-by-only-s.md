---
id: sched-20261118-017
date: '2026-11-18'
subject: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <20261111110409.1498035-1-luogengkun@huaweicloud.com>
lore_url: https://lore.kernel.org/all/20261111110409.1498035-1-luogengkun@huaweicloud.com/
authors:
- Luo Gengkun
maintainers_involved:
- Peter Zijlstra
- Tim Chen
current_version: v11
patch_series:
- version: v11
  msgid: <20261111110409.1498035-1-luogengkun@huaweicloud.com>
  date: '2026-11-11'
  summary: visited_cpus 精确追踪扫描范围，移除 get_scan_cpumasks
  review_outcome: 合入 tip/sched/core；Tim 指出 subject 拼写笔误
upstream_commit: 953f9fc86e54bf0debeb3f83e3e28ace167175e1
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 观察是否随 sched/core 进入下一 mainline 合入窗口
contribution_opportunities:
- kind: testing
  description: 多 NUMA 平台复跑 valkey-benchmark 验证长期运行稳定性
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261109-015
tags:
- cgroup
- load_balance
- numa_balancing
- perf
title: 'sched/cache: Reduce the overhead of task_cache_work by only scan the visisted
  cpus'
layout: article
---

## TL;DR

Luo Gengkun（华为）的 `task_cache_work()` 开销优化**今日被合入 tip/sched/core**（commit `953f9fc86e54`，Committer Peter Zijlstra）：用 `visited_cpus` 追踪已访问 CPU 并按 `llc_epoch_affinity_timeout` 淘汰，避免多 NUMA 系统上扫描全量 CPU，随之删除 `get_scan_cpumasks()`。附带 Redis/valkey 测试数据。Tim Chen 当日另发一帖指出 commit message 里 "visisted" 为 "visited" 的拼写笔误。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-015-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261109-015</a>）cache-aware scheduling 的 `task_cache_work()` 之前要扫描系统所有 CPU 来寻找 `pref_llc`，在多 NUMA 系统上开销过高，且大多数扫描无意义（从未访问或久未访问的 CPU）。作者通过 `visited_cpus` 精确追踪需扫描的 CPU 集合并按时淘汰，收敛扫描范围。

## 技术方案

（承接）引入 `visited_cpus` 记录访问过的 CPU，超时（`llc_epoch_affinity_timeout`）未访问即淘汰；据此可精确知道要扫描哪些 CPU，进而移除 `get_scan_cpumasks()`。今日：合入 tip/sched/core，附带 Redis/valkey-benchmark 在 AMD 服务器上的对照数据。

## 版本演进与当前进展

*current_version: v11（2026-11-11 发出，`<20261111110409.1498035-1-luogengkun@huaweicloud.com>`）*。今日：**已合入 tip/sched/core**（`953f9fc86e54`，AuthorDate 2026-11-11，CommitterDate 2026-11-18）；Tim Chen 发帖纠正 subject 的 "visisted"→"visited" 拼写。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：作为 Committer 合入 tip/sched/core。
- **Tim Chen（sched/cache 维护者）**：指出 "visisted" 是笔误、应为 "visited"（属 commit message 措辞，不影响代码）。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/core（`953f9fc86e54`）。*blocking_issues*：无；commit message 的拼写笔误可在后续 commit 修正。*next_action*：观察是否随 sched/core 进入下一合入窗口的 mainline。

## 效果评估

作者在 AMD 服务器上的 Redis/valkey-benchmark 测试（禁用 NUMA balancing）给出 rps 对照：baseline（无 cache aware）、schedcache（无此系列）、schedcache_visit（有此系列）三列数据（见 commit message），本系列以更少扫描维护相当性能。

## 我可以参与的点

- **testing**：在单 LLC 多 NUMA 平台上复跑 valkey-benchmark，验证 `visited_cpus` 淘汰策略在长时间运行下的性能稳定性。

## 参考链接

- tip 合入: https://git.kernel.org/tip/953f9fc86e54bf0debeb3f83e3e28ace167175e1
- lore thread: https://lore.kernel.org/all/20261111110409.1498035-2-luogengkun@huaweicloud.com/
- Tim 的拼写纠正: https://lore.kernel.org/all/1989e04ee420925b88ec5f17c6fbd11f06739ffd.camel@linux.intel.com/
