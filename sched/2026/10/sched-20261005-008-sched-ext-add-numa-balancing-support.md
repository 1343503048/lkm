# sched_ext: Add NUMA balancing support

> **subject**：`sched_ext: Add NUMA balancing support`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261002-014：Vladimir Vdovin 的单片 RFC——自动 NUMA balancing 对 sched_ext 任务**事实性关闭**：扫描只从 fair tick 排队，SCX 任务 `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、跑在 preferred nid 比例 37%（fair 83%）。Andrea Righi（sched_ext 维护者）回复 backlog 里正有一套 sched_ext NUMA balancing 支持，将发到列表；Vladimir 撤下自己的 sketch 转做测试员。
- sched-20261004-001：**Andrea 兑现承诺，发出 5 补丁系列**（`[PATCHSET sched_ext/for-7.4]`）：`SCX_OPS_NUMA_BALANCING` opt-in 让 BPF 调度器为任务请求 NUMA hinting-fault 扫描，扫描从 sched_ext tick 驱动（与 `task_tick_fair()` 同构），fault 记账/preferred node/内存迁移照常、任务放置留给 BPF；`scx_bpf_task_numa_nid()` 把 preferred node 暴露给 BPF；3/5 带 `Reported-by: Vladimir Vdovin`。
- sched-20261005（今天）：Vladimir 开始履行测试员角色，对 3/5（scan NUMA hinting faults）提出**proxy execution 语义问题**：本补丁从 **donor** 驱动扫描，而 Hui Su 的 tick 系列把 fair NUMA tick 移到**执行上下文**（理由是 `task_tick_numa()` 作用于实际运行任务的 mm 与 NUMA work 状态）——SCX runtime 记在 donor 上、pacing 一致或许是有意为之，但那样扫描覆盖的是 donor 的地址空间而非被访问的地址空间；询问 donor 是否就是 intended choice，还是应等 `SCHED_PROXY_EXEC` 不再依赖 `!SCHED_CLASS_EXT` 后改随 `rq->curr`。Andrea 当日未回。

## 背景与问题

（承接 sched-20261002-014 → sched-20261004-001）BPF 调度器下的任务对 NUMA balancing 不可见：周期性扫描只从 fair tick（`task_tick_fair()` → `task_tick_numa()`）排队，SCX 任务的地址空间从不被扫描 hinting fault、preferred node 冻结——BPF 调度器决定任务放置时拿不到「任务的内存在哪」。Vladimir 的 KVM 宿主机实测：SCX 下 `numa_pte_updates/s = 0`、58% 任务无 preferred_nid、跑在 preferred nid 37% vs fair 83%。Andrea 的 5 补丁系列以 opt-in 方式补齐扫描与 preferred node 暴露。今天的新问题在 **proxy execution 交互**：proxy execution 下 donor（调度上下文）与 curr（执行上下文）分离，3/5 的扫描驱动点选了 donor——若被 proxy 的执行者实际访问的是另一个地址空间（mutex owner 场景），扫描与真实访存脱节；这与 fair 侧 Hui Su tick 系列「NUMA tick 移到执行上下文」的处理方向相反。

## 技术方案

（承接）5 补丁（`<20261004072901.3579967-{1..6}-arighi@nvidia.com>`）：1/5 通用 NUMA 代码开放非 fair 调度类驱动扫描；2/5 任务放置留给 BPF 调度器；3/5 `SCX_OPS_NUMA_BALANCING` opt-in + 从 sched_ext tick 驱动扫描（空间节奏用 `p->se.sum_exec_runtime`）；4/5 `scx_bpf_task_numa_nid()` kfunc；5/5 selftest。

今天的讨论（Vladimir，`<DLWVCRDZK3XK.1JG5J57YQV0VI@verdict.gg>`）不改代码，提出 3/5 扫描驱动点的 donor/curr 选择问题：

- 引用 Hui Su 的 fair tick 系列（`<20260909092901.2989564-3-sh_def@163.com>`）：fair NUMA tick 移到执行上下文，因为 `task_tick_numa()` 作用于「实际运行任务的 mm 和 NUMA work 状态」。
- 3/5 从 donor 驱动。Vladimir 推测的可能理由：SCX 的 runtime 记账在 donor 上（`update_curr_common()` 维护 `sum_exec_runtime`），扫描节奏（pacing）保持一致；但代价是**扫描覆盖 donor 的地址空间而非被实际访问的地址空间**。
- 开放问题：donor 是 intended choice，还是应随 `rq->curr`（等 `SCHED_PROXY_EXEC` 不再依赖 `!SCHED_CLASS_EXT`、两者可共存之后）？

## 版本演进与当前进展

- Vladimir RFC（10-02，单片 sketch）：让位给 Andrea 系列（sched-20261002-014）。
- 系列本 v1（10-04，5 补丁，`sched_ext/for-7.4`）（sched-20261004-001）。
- 10-05（今天）：Vladimir 首 review——proxy execution 下 donor vs 执行上下文的扫描驱动点问题。Andrea 未回；Tejun 未现。

## Maintainer 意见与讨论焦点

- **Vladimir Vdovin**（原报告者、现测试员）：问题质量高——直接命中 proxy execution 与 sched_ext 合流（`SCHED_PROXY_EXEC` 当前依赖 `!SCHED_CLASS_EXT`，两特性暂互斥）的时间窗问题：现在选 donor 还是先定「共存后随 curr」。
- **Andrea Righi**（作者、sched_ext 维护者）：当日未回。
- **Tejun Heo**（sched_ext 顶层维护者）：未现——3/5 动 `task_tick_numa()` 驱动路径，其 review 是合入关口。
- 焦点：扫描驱动语义（donor vs curr）与 SCX runtime 记账语义（记 donor）的一致性问题——若 runtime 记 donor 而扫描须随 curr，则 `sum_exec_runtime` 节奏与扫描主体错位，需要 Andrea 明确设计意图。

## 合入评估

*likelihood=medium*。作者即分支维护者、有外部触发者深度参与；但 3/5 的 donor/curr 选择在被 proxy 场景挑战后可能需要调整或至少补说明，且 Tejun/Mel 侧 review 未开始。*blocking_issues*：donor vs 执行上下文的扫描驱动点待作者澄清/修正；Tejun 与 NUMA 侧维护者 review 未开始。*next_action*：Andrea 回应 donor 问题（解释或改随 curr/补 proxy 场景说明）；Vladimir 的 2/4 节点测试数据待交。

## 效果评估

本日无新数据。既有（Vladimir，6.18.5、2 节点 160-CPU KVM 宿主机）：SCX `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、无 preferred_nid 58%（fair 5 分钟后 10%）、跑在 preferred nid 37%（fair 83%）。

## 我可以参与的点

- `discussion`：在 Vladimir 的问题上补一层数据——proxy execution 与 SCX 目前互斥（`SCHED_PROXY_EXEC` 依赖 `!SCHED_CLASS_EXT`），当前合入版本实际不会出现「SCX 任务被 proxy」的场景，donor/curr 选择眼下是**前瞻性**而非现实 bug；把这个时间窗事实摆清楚可帮讨论收敛到「先记录意图、共存时再修」。
- `review`：3/5 的 `sum_exec_runtime` 节奏论证——SCX 下该字段由 `update_curr_common()` 维护在 donor 上，若将来随 curr 扫描，节奏与主体的错位如何影响 `task_numa_work()` 的采样密度，可给 Andrea 的答复提供输入。

## 参考链接

- Vladimir 的 donor/curr 问题: https://lore.kernel.org/all/DLWVCRDZK3XK.1JG5J57YQV0VI@verdict.gg/
- Andrea 系列 cover: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
- Hui Su fair NUMA tick 系列（被引用）: https://lore.kernel.org/r/20260909092901.2989564-3-sh_def@163.com
- Vladimir 原 RFC: https://lore.kernel.org/all/20261002124559.10367-1-deliran@verdict.gg/

---
id: sched-20261005-008
date: '2026-10-05'
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched_ext
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261004072901.3579967-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/DLWVCRDZK3XK.1JG5J57YQV0VI@verdict.gg/'
authors:
  - 'Andrea Righi'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261004072901.3579967-1-arighi@nvidia.com>'
    date: '2026-10-04'
    summary: 'SCX_OPS_NUMA_BALANCING opt-in 扫描 + scx_bpf_task_numa_nid() + selftest'
    review_outcome: '10-05 Vladimir 提 proxy execution 下 donor vs 执行上下文的扫描驱动点问题'
related_articles:
  - sched-20261002-014
  - sched-20261004-001
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: 'donor/curr 扫描驱动点待澄清；Tejun 与 NUMA 侧维护者 review 未开始'
  next_action: 'Andrea 回应 donor 问题；Vladimir 交多节点测试数据'
generated_at: '2026-10-06T01:00:00'
tags:
  - sched_ext
  - numa
  - bpf
---
