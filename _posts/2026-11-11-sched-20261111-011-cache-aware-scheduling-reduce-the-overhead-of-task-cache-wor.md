---
id: sched-20261111-011
date: '2026-11-11'
subject: 'Cache aware scheduling: Reduce the overhead of task_cache_work'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261111110409.1498035-1-luogengkun@huaweicloud.com>
lore_url: https://lore.kernel.org/all/20261111110409.1498035-1-luogengkun@huaweicloud.com/
authors:
- Luo Gengkun
maintainers_involved: []
current_version: v11
patch_series:
- version: v11
  msgid: <20261111110409.1498035-1-luogengkun@huaweicloud.com>
  date: '2026-11-11'
  summary: visited_cpus 追踪 + 超时驱逐，移除 get_scan_cpumasks；benchmark 并入 commit message
  review_outcome: Prateek Tested-by、Chen Yu R-b/T-b；等维护者收取
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: sched 维护者收取 v11
contribution_opportunities:
- kind: testing
  description: 在单 node 多 LLC/非对称核拓扑上复跑 valkey-benchmark 与 hackbench 验证精度
- kind: review
  description: 复核 llc_epoch_affinity_timeout 驱逐是否误伤低频持续访问的 CPU
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 3
related_articles:
- sched-20261021-010
- sched-20261022-012
- sched-20261109-015
tags:
- cfs
- numa_balancing
- perf
title: 'Cache aware scheduling: Reduce the overhead of task_cache_work'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-010-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261021-010</a>：Luo Gengkun（华为）的系列（task_cache_work 只扫访问过的 CPU）推进到 v10；K Prateek Nayak 在 4 代 EPYC 上实测给 Tested-by，并建议把 benchmark 数字放进 commit message。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-012-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261022-012</a>：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench 后给 Reviewed-by + Tested-by；Tim Chen 提两处注释/死代码 nit。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-015-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261109-015</a>：作者出差归来，逐条回应三位 reviewer（接受 Tim 注释与「删冗余 continue」、致谢 Chen Yu、承诺把 Prateek 性能数字写进 commit message 并加其 Tested-by）。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-011-cache-aware-scheduling-reduce-the-overhead-of-task-cache-wor.html">sched-20261111-011</a>（今天）：**v11 发出**——正式引入 `visited_cpus` 追踪访问过的 CPU 并按 `llc_epoch_affinity_timeout` 驱逐久未访问者，从而移除 `get_scan_cpumasks()`；benchmark 数字已写进 commit message。AMD 上 valkey-benchmark 400k rps：NUMA off 时 task_cache_work 开销 0.81%→0.02%、p99 回归从 -25.68% 收窄到 -1.14%；NUMA on 时 0.13%→0.03%、p99 -3.89%→-1.14%；hackbench 无精度回退。附 patch 2/2 为「DO NOT APPLY」的 debug trace 补丁（`sched_cache_scan` tracepoint + `SC_VISIT` sched feature）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-010-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.html">sched-20261021-010</a> / 20261022-012 / 20261109-015）`task_cache_work()` 周期性扫描 CPU 维护 cache 感知聚合的 footprint，v10 起只扫描「访问过的 CPU」以降开销。在多 NUMA 系统上，task_cache_work 原来要扫全系统所有 CPU，其中绝大多数扫描（从未访问、或久未访问的 CPU）是无意义的，这正是 Redis 等多实例场景 p99 延迟被拖累的根源。

## 技术方案

v11 的 patch 1/2 `Reduce the overhead of task_cache_work by only scan the visited cpus`：

- 新增 `visited_cpus` 位图追踪被访问过的 CPU，超过 `llc_epoch_affinity_timeout` 未再访问的 CPU 被驱逐（evict）。
- 有了精确的「该扫哪些 CPU」后，删除旧的 `get_scan_cpumasks()`（原逻辑是扫全系统或按 NUMA 节点拼 mask）。
- patch 2/2（`-- DO NOT APPLY!!! --`）为 debug 辅助：重加 `get_scan_cpumasks()` 并引入两个 sched feature（`SC_VISIT` 等）与 `sched_cache_scan` tracepoint，用于对比扫描开销；明确标注「勿应用」。

## 版本演进与当前进展

*current_version: v11（2026-11-11，`<20261111110409.1498035-1-luogengkun@huaweicloud.com>`）*。v11 落实 v10 评审承诺：benchmark 数字并入 commit message、加 Prateek 的 Tested-by；机制从「去掉 get_scan_cpumasks」演进为「visited_cpus 追踪 + 超时驱逐 + 移除 get_scan_cpumasks」。当日无新回复。

## Maintainer 意见与讨论焦点

当日无新维护者回复。既有背书：K Prateek Nayak（EPYC）Tested-by、Chen Yu（Xeon 多 LLC）Reviewed-by + Tested-by，Tim Chen 两处注释/死代码 nit 已在 v11 前被采纳。无 NAK，无未解决分歧。

## 合入评估

*likelihood=high*。双平台 Tested-by + 一个 Reviewed-by，且 reviewer 要求的 benchmark 已并入 commit message，处于「等维护者收取」状态。*blocking_issues*：无实质阻塞。*next_action*：sched 维护者（Peter/Ingo 或 cache-aware 相关维护者）收取 v11。

## 效果评估

作者给出 AMD 服务器上 valkey-benchmark 400k rps 的数据（NUMA balancing 关/开两档）：task_cache_work 的 `perf top -e cycles:k` 开销 0.81%→0.02%（关）与 0.13%→0.03%（开）；p99 延迟相对无 cache-aware 的 baseline 从「无本系列时 -25.68%/-3.89%」收窄到「有本系列时 -1.14%/-1.14%」；trace 显示单次扫描的 CPU 数从 384 降到 13-16。hackbench 对比显示系列不损害 cache-aware 调度的精度。

## 我可以参与的点

- **testing**：在更多 NUMA 拓扑（尤其单 node 多 LLC、或非对称核）上复跑 valkey-benchmark/hackbench，确认 visited_cpus 驱逐阈值在极端工作负载下无精度回退。
- **review**：复核 `llc_epoch_affinity_timeout` 驱逐语义是否可能过早驱逐「低频但持续」的 CPU，导致 footprint 精度退化。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111110409.1498035-1-luogengkun@huaweicloud.com/
- patch 1/2: https://lore.kernel.org/all/20261111110409.1498035-2-luogengkun@huaweicloud.com/
