# sched/cache: Remove the old cache group footprint on exec

> **subject**：sched/cache: Remove the old cache group footprint on exec

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261009-007 / 20261010-003：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换掉 cache group 后旧 group 的 footprint 只在 exit 路径被减，共享 mm 任务 exec 后旧贡献残留；v2 抽 helper 让 exec 与 exit 都 drop。
- sched-20261012-008：Chen Yu 指出 footprint 无锁读写的竞态；Jemmy 折入 `try_cmpxchg_relaxed()` 等改进，并反问 clamp 是否会掩盖记账 bug。
- sched-20261014-010（今天）：Jemmy 回应 clamp 疑问——改走 **`atomic_long_t` footprint + `atomic_long_add/sub`**，**去掉 clamp**，并按 Chen Yu 建议「每次 placement pass 只更新一次 footprint」（placement 前快照 `total_numa_faults`、循环后结净差）。附一份「exec 失败后的新 group 可能短暂为负」的例外分析，请 Chen Yu 确认该方向。

## 背景与问题
（承接 20261009-007/20261012-008）`grp->footprint` 记录每个任务对该 cache group 的 NUMA fault 贡献，退出/exec 时应减掉。此前实现用 `READ_ONCE()/WRITE_ONCE()` 无锁更新并 clamp 防下溢，Chen Yu 指出存在竞态；Jemmy 上轮反问「clamp 是否掩盖贡献不平衡的记账 bug」。今日聚焦该问题的收口。

## 技术方案
（承接 v2）Jemmy 把 `grp->footprint` 改为 `atomic_long_t`：`sched_cache_footprint_update()` 用 `atomic_long_add(delta)`（placement 净差）、离开 group（exec/exit）用 `atomic_long_sub(p->total_numa_faults)`；`exceed_llc_capacity()` 读 `atomic_long_read` + `WARN_ON_ONCE(fp < 0)` + `max(fp, 0L)` 兜底。**移除 clamp** 的理由：footprint 聚合的正是 `p->total_numa_faults` 追踪的同一批贡献，NUMA placement 本就对逐节点计数与任务总量做带符号增量而不 clamp；负增量只是「半个 bucket 的衰减」，正常 decay 不会把某任务贡献变成负；原子更新避免丢 delta、去组任务只减一次，footprint 理应非负（假设无溢出），clamp 反而会掩盖记账 mismatch。同时采纳 Chen Yu 的「每 pass 更新一次」：placement 前快照 `p->total_numa_faults`、循环后结 `total - old` 净差，复用既有 NUMA 计数、减少共享 cacheline 流量。

一处例外：exec 在换组后、`task_numa_free()` 重置前失败，exit 会从新 group 减去从未计入的旧 total，使新 group 短暂为负——但该组只属这个即将 exit 的 exec 任务、不会在存活共享组中残留。

## 版本演进与当前进展
v2（10-10）→ 今日（10-14）Jemmy 折入 atomic_long_t + 去 clamp 方案并请 Chen Yu 确认，尚未定稿 v3。

## Maintainer 意见与讨论焦点
- **Chen Yu**（前轮）：指出无锁竞态、建议每 pass 更新一次——今日方案已采纳。
- **Jemmy Wong**（作者，今日）：给出「atomic_long_add/sub（无序）替代 CAS 循环 + 去 clamp」的完整论证，并主动标注 failed-exec 的负值例外。
- 焦点已从「是否竞态」推进到「atomic_long_t 无 clamp 是否可接受 + failed-exec 边缘」，仍待 Chen Yu 确认。

## 合入评估
*likelihood=medium*。方向稳定、原子化方案自洽且有失败路径分析，但 Chen Yu 尚未确认「atomic_long_t + 无 clamp」这个关键取舍，无 RB。*blocking_issues*：待 Chen Yu 确认无 clamp 方向；failed-exec 负值例外的可接受性。*next_action*：Chen Yu 确认后 Jemmy 发 v3。

## 效果评估
无性能数字；作者提到「placement 快照 + 净差」复用既有 NUMA 计数以减少共享 cache-line 流量，属机制性收益，无量化。

## 我可以参与的点
- review：评估 `atomic_long_add/sub` 无序语义是否足以保证 footprint 在 placement/exec/exit 三处并发下不丢 delta，以及 failed-exec 负值例外是否会被 `WARN_ON_ONCE(fp < 0)` 误报。
- testing：在含 NUMA balancing + CONFIG_SCHED_CACHE 的机器上对 exec/exit 压力场景观测 `grp->footprint` 是否保持非负。

## 参考链接
- v2 lore：https://lore.kernel.org/all/20261010111612.31345-1-jemmywong512@gmail.com/
- 今日 Jemmy 更新：https://lore.kernel.org/all/32BC7D58-C1C9-4B24-857B-7433F19606A8@gmail.com/

---
id: sched-20261014-010
subject: 'sched/cache: Remove the old cache group footprint on exec'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261010111612.31345-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20261010111612.31345-1-jemmywong512@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved:
  - 'Chen Yu'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20261010111612.31345-1-jemmywong512@gmail.com>'
    date: 2026-10-10
    summary: 'exec 路径也 drop 旧 cache group footprint，抽 helper 与 exit 共用'
    review_outcome: 'Chen Yu 指出竞态；Jemmy 折入 atomic_long_t 去 clamp 方案，待陈确认'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Chen Yu 尚未确认 atomic_long_t 无 clamp 方向'
    - 'failed-exec 负值例外的可接受性'
  next_action: 'Chen Yu 确认后发 v3'
contribution_opportunities:
  - kind: review
    description: '评估 atomic_long_add/sub 无序语义在 placement/exec/exit 并发下的完备性'
  - kind: testing
    description: 'NUMA balancing + CONFIG_SCHED_CACHE 下观测 footprint 是否保持非负'
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261009-007
  - sched-20261010-003
  - sched-20261012-008
tags: [load_balance, numa_balancing]
---