---
id: sched-20261009-006
date: '2026-10-09'
subject: 'Cache aware scheduling: Reduce the overhead of task_cache_work'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261009032943.95091-1-luogengkun@huaweicloud.com>
lore_url: https://lore.kernel.org/all/20261009032943.95091-1-luogengkun@huaweicloud.com/
authors:
- Luo Gengkun
maintainers_involved: []
current_version: v10
patch_series:
- version: v10
  msgid: <20261009032943.95091-1-luogengkun@huaweicloud.com>
  date: '2026-10-09'
  summary: visited_cpus 只扫访问过的 CPU + 超时驱逐，移除 get_scan_cpumasks()
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - v10 当日无 review
  - visited_cpus 驱逐/并发语义待确认
  next_action: 等维护者 review v10 扫描范围与驱逐策略
contribution_opportunities:
- kind: testing
  description: 华为多 NUMA 服务器复跑 Redis 多实例 p99 与 CPU 开销
- kind: review
  description: 审 visited_cpus 驱逐与 get_scan_cpumasks 移除后的正确性
generated_at: '2026-10-10T01:30:00'
source_email_count: 4
related_articles:
- sched-20260731-006
tags:
- load_balance
- numa_balancing
title: 'Cache aware scheduling: Reduce the overhead of task_cache_work'
layout: article
---

## TL;DR
Luo Gengkun（华为）发 v10，通过只扫描「被访问过的 CPU」（`visited_cpus`、超时驱逐）来降低 `task_cache_work()` 的扫描开销，并顺势移除 `get_scan_cpumasks()`。valkey-benchmark 实测：Redis 多实例场景 p99 时延从（未合本系列时更差的）-25.68% 收窄到 -1.14%，`task_cache_work` 的 perf 开销从 0.81% 降到 0.02%，扫描 CPU 数从 384 降到 16。当日无回帖；另附 0day 对已合入 sched/cache UAF 修复提交的独立实测（+5.2%）作为同子系统背景。

## 背景与问题
`task_cache_work()` 在多 NUMA 系统上开销高：它通过扫遍系统所有 CPU 来找 `pref_llc`。但大多数扫描无意义（从未被访问过的 CPU、或很久以前访问过的 CPU）。多实例场景（如 Redis）下这一开销尤其明显。

## 技术方案
引入 `visited_cpus` 跟踪被访问过的 CPU，超过 `llc_epoch_affinity_timeout` 未被访问即驱逐。既然能精确知道要扫哪些 CPU，即可移除 `get_scan_cpumasks()`。改动落在 `include/linux/sched.h`（`sched_cache_group` 加 `visited_cpus`、`sched_cache_time` 加 `epoch_last_visit`）与 `kernel/sched/fair.c`（+55/-64，含 `mm_init_sched` 分配 visited_cpus 与新的错误清理路径）。附一枚「DO NOT APPLY」的 debug 补丁（trace event + sched feature）供测试。

## 版本演进与当前进展
*current_version: v10*（`<20261009032943.95091-1-luogengkun@huaweicloud.com>`，0/2 + 1/2 + debug 2/2）。该系列最早于 7 月以 v9 出现（见 <a class="article-ref" href="/lkm/2026/07/31/sched-20260731-006-sched-cache-task-cache-work-v9.html">sched-20260731-006</a>），今隔近三个月发 v10。当日无回帖、尚无新版本的维护者意见。

## Maintainer 意见与讨论焦点
当日无回帖，无维护者（Peter/Vincent 或 cache-aware 系列相关 reviewer）本日表态。v9→v10 的演进方向（visited_cpus 取代全量扫描）需等新一轮 review 确认。

## 合入评估
*likelihood=medium*。系列已迭代到 v10、有明确的 Redis 多实例数据支撑，说明方向经过多轮打磨；但当日无回帖，且 cache-aware 系列历史上合入门槛（LLC 扫描语义、与 NUMA balancing 的交互）较高。*blocking_issues*：① v10 当日无 review；② 需确认 `visited_cpus` 驱逐逻辑与并发更新在多 NUMA 下的正确性。*next_action*：等维护者对 v10 的扫描范围缩减与驱逐策略 review。

## 效果评估
作者在 AMD 服务器上给出 Redis（valkey-benchmark，400000 rps，NUMA balancing 关闭）数据：

- p99 时延：baseline 0.436ms；schedcache（无本系列）0.554ms（-25.68%）；schedcache_visit（含本系列）0.441ms（-1.14%）。
- `perf top -e cycles:k` 的 `task_cache_work` 开销：0.81% → 0.02%。
- trace：`sched_cache_scan` 的 `scan=` 从 384 降到 16。

作者另注 NUMA balancing 开启时本补丁收益更佳（数据未在本次读取范围内完整展开）。

相关背景：0day 对已合入 mainline 的 `28f9c0e0a0`（"sched/cache: Decouple sched_cache_group from mm to fix UAF"）与 `d6013e2465` 的独立实测显示 stress-ng fd-race `ops_per_sec` +5.2%（256 线程 Sierra Forest），说明该子系统的修复/优化已开始兑现到真实负载。

## 我可以参与的点
- `testing`：在华为多 NUMA 服务器上复跑 Redis/valkey 多实例场景，验证 v10 在真实业务混合负载下的 p99 时延与 CPU 开销。
- `review`：审 `visited_cpus` 的驱逐与「长时间未访问」判定在多 NUMA 下与 `llc_epoch_affinity_timeout` 的交互、以及 `get_scan_cpumasks()` 移除后的负载均衡正确性。

## 参考链接
- 系列 cover (v10): https://lore.kernel.org/all/20261009032943.95091-1-luogengkun@huaweicloud.com/
- 0day 实测报告: https://lore.kernel.org/all/202610091149.c00cf9f2-lkp@intel.com/
