# sched/cache: Reduce the overhead of task_cache_work by only scan the visisted cpus

## TL;DR
本文为增量更新，完整脉络见下。

- sched-20260911-011：Luo Gengkun（华为）对 v9 系列友好 ping——所有 review 意见已解决，询问 Tim Chen 是否可收取；该系列（task_cache_work 只扫访问过的 CPU）自 07-31 v9 后沉默六周，维护者未表态，按停滞（stalled）归并。
- sched-20261021-010（今天）：系列已推进到 **v10**（2 补丁，20261009 发出）；K Prateek Nayak 评审 1/2，在 4 代 EPYC（2×128C/256T）上实测后给出 *Tested-by*——hackbench/tbench/stream/netperf/schbench 整体无超出 run-to-run 方差的回退、有小的提升；并提一个 nit（把 cover letter 的性能数据放进 commit message 存档）。

## 背景与问题
（承接 sched-20260911-011）cache-aware scheduling 的 `task_cache_work`（per-task 周期性缓存统计）扫描全部 CPU，开销与 CPU 数成正比；方案用 `for_each_cpu_and` 结合 `visited_cpus` 位图只扫实际访问过的 CPU，去掉 `get_scan_cpumasks()`。今日无背景新增，进展集中在「补丁获得外部实测背书」。

## 技术方案
（承接 sched-20260911-011 的 v8/v9）核心仍是 `for_each_cpu_and` + `visited_cpus` 只扫访问过的 CPU；并发安全已由 Chenyu 确认（`try_cmpxchg` 保证同一时刻只有一个 scanner）。今日无新代码，仅评审反馈：K Prateek 建议在 1/2 的 commit message 里附上 cover letter 的 benchmark 数字存档，并给 Tested-by。

## 版本演进与当前进展
*current_version: v10*（2 补丁，`<20261009032943.95091-2-luogengkun@huaweicloud.com>` 为 1/2）。

## Maintainer 意见与讨论焦点
K Prateek Nayak（AMD）：ET EPYC 实测小提升、无超方差回退，给 Tested-by；nit 是让 commit message 带上 cover 的性能数据。Tim Chen（原始评审者）本日无表态。尚无 sched 维护者（Peter/Vincent/Ingo）结论。

## 合入评估
*likelihood=medium*。从停滞推进到「外部 Tested-by」是积极信号，但距离维护者收取仍缺 Tim Chen 的收尾确认或 Peter/Vincent 的 Ack。*blocking_issues*：需把性能数据并入 commit message 后重新确认；无维护者结论。*next_action*：作者按 nit 更新 commit message，推动 Tim Chen / 维护者收取。

## 效果评估
K Prateek Nayak 在 AMD 4 代 EPYC 上给出完整 benchmark（hackbench、tbench、stream-10/100、netperf、schbench 及 new-schbench 多项）：整体为「小提升、无超出 run-to-run 方差的回退」，例如 schbench 部分 worker 点的 99th 延迟有 7%–24% 改善，但个别点（如 2-worker -16.67%）在噪声范围内。数据支撑充分。

## 我可以参与的点
- `testing`：在 Intel 平台（作者与 Tim Chen 视角）或不同 NUMA 拓扑上复测 v10，补充跨平台数据加速收取。
- `review`：检查 1/2 的 commit message 是否已含 cover 的 benchmark 数字（K Prateek 的 nit）。

## 参考链接
- K Prateek Nayak 的 Tested-by 与 benchmark：https://lore.kernel.org/all/1e9259b5-0758-4387-a572-37e2d32c47c0@amd.com/
- v10 1/2 patch：https://lore.kernel.org/all/20261009032943.95091-2-luogengkun@huaweicloud.com/

---
id: sched-20261021-010
date: 2026-10-21
subject: "sched/cache: Reduce the overhead of task_cache_work by only scan the visisted cpus"
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20261009032943.95091-2-luogengkun@huaweicloud.com>"
lore_url: "https://lore.kernel.org/all/20261009032943.95091-2-luogengkun@huaweicloud.com/"
authors: ["Luo Gengkun"]
maintainers_involved: []
current_version: v10
patch_series:
  - version: v10
    msgid: "<20261009032943.95091-2-luogengkun@huaweicloud.com>"
    date: 2026-10-09
    summary: "task_cache_work 只扫访问过的 CPU（for_each_cpu_and + visited_cpus）"
    review_outcome: "K Prateek Nayak EPYC 实测 Tested-by，nit 建议 commit message 带性能数据"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["缺 Tim Chen / sched 维护者收尾确认"]
  next_action: "作者按 nit 更新 commit message 后推动收取"
contribution_opportunities:
  - kind: testing
    description: "在 Intel 平台或不同 NUMA 拓扑复测 v10，补充跨平台数据"
  - kind: review
    description: "核对 1/2 commit message 是否已含 cover benchmark 数字"
generated_at: "2026-10-22T01:30:00"
source_email_count: 1
related_articles: ["sched-20260911-011"]
tags: [cfs, numa_balancing]
---