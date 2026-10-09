# sched/eevdf: Add min slice check when selecting CPU

> **subject**：`sched/eevdf: Add min slice check when selecting CPU`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-018：Vincent Guittot 8 补丁系列「Improving latency of short slice tasks」的 patch 8/8——`select_task_rq_fair()` 找不到空闲 CPU 时新增 `select_slice_cpu()` 比较候选 CPU 的 slice，避免短 slice 任务被放到已运行同长或更短 slice 任务的 CPU 上；Peter 建议复用初次扫描、Kayra 质疑 `nr_idle_scan` 语义，Vincent 确认注释需更新并宣布与 idle CPU 搜索合并。
- sched-20261001-010：Christian Loehle 建议 8/8 之上再叠加「选 `current->vprot - current->vruntime` 最小的 rq」维度，并点出代价（会再次抑制长 slice 任务）、希望看到真实负载下不同 slice 长度的表现。
- sched-20261002-001（今天）：Vincent 把 8 补丁 v1 扩张成 **18 补丁 v2** 重发——`select_slice_cpu()` 已按其承诺并入 `select_idle_capacity()` 与 `select_idle_cpu()`；系列同时吸收 lag 管理（睡眠实体正 lag 衰减、idle CPU 唤醒重置 lag）、per-cpu min_slice 缓存、wake_affine min slice 比较，并新增 fair 的 **push task 机制**（pushable_tasks plist + move_queued_task 导出，供 EAS/短 slice 任务主动推走）与 **feec() 重构**（用 OPP cost 而非 spare capacity 选 CPU、EAS 计入 slice）。对 Christian 的 vprot-vruntime 维度，Vincent 回复「不持锁读不到 current->vprot/vruntime」而未采纳。15/18、17/18 两封未进当日缓存。

## 背景与问题

（承接 sched-20260929-018）EEVDF 下短 slice 任务在 `select_task_rq_fair()` 找不到空闲 CPU 时，可能被放到已运行同长或更短 slice 任务的 CPU 上导致显著等待。v1 的 8 补丁系列「Improving latency of short slice tasks」（09-21，sched-20260921-001）以 `select_slice_cpu()` 在选 CPU 最后阶段加 min slice 检查。v2 的扩张背景是：短 slice 任务除了「放置时不挑 CPU」，还有「放错了之后无人推走」的第二阶段问题——EAS 只在 wakeup 事件驱动下生效，任务若无 wakeup（或 wakeup 频率过低）就一直困在次优 CPU 上；同时 v1 只优化了放置，未处理睡眠任务的正 lag 在醒来时延续、以及多个任务同时唤醒到 idle CPU 时 vlag 取决于加锁顺序的不确定性。

## 技术方案

v2 共 18 补丁（系列 cover `<20261002154415.2270586-1-vincent.guittot@linaro.org>`，当日缓存收到 16 封，15/18 与 17/18 缺失）。主要分组：

**lag 管理**
- 01/18 `Decay positive lag of sleeping entities`：`decay_entity_lag()` 在 wakeup 时按睡眠时长把正 vlag 衰减掉（睡眠越久扣得越多，超过 4 秒清零；负 lag 不动），`se->vlag = max(0, vlag)`。
- 02/18 `Reset lag when waking up on idle cpu`：idle CPU 上的 enqueue 直接把 vlag 清零——否则 TA(vlag 0ms)/TB(vlag 5ms) 同时唤醒时谁先抢到锁决定了最终 vlag；新增 `se->vlag_seq`/`cfs_rq->idle_seq`，cfs_rq 清空时 idle_seq++，enqueue 发现序列不匹配（中间空过）也清零。

**min slice 选 CPU（v1 主体重构）**
- 03/18 `Add per cpu cached min_slice`：per-cpu 缓存 rq 的最小 slice，避免选 CPU 路径反复遍历。
- 04/18 `Compare min slice during wake_affine`：wake_affine 判定也纳入 min slice 比较。
- 05/18 `Add min slice check when selecting CPU`：把 `select_slice_cpu()` 并入 `select_idle_capacity()` 与 `select_idle_cpu()`（落实 09-29 对 Peter「与 select_idle_sibling() 重复」意见的承诺）。
- 06/18 `Prepare select_task_rq_fair() to be called for new cases`、11/18 `Support not wakeup case in select_idle_sibling`：为「非 wakeup 路径调用选 CPU」铺路。

**push task 机制（新增）**
- 07/18 `Add push task mechanism for fair`：rq->cfs 增加 `pushable_tasks` plist；把 `move_queued_task()` 从 core.c 静态导出；任务被放回 enqueued list 时检查是否应推到别的 CPU——「EAS will be one user but other feature like filling idle CPUs or short slice tasks can also take advantage of it」。
- 08/18 `Optimize push task mechanism for fair`、09/18 `Add rq flag to tick parameters`、10/18 `Add force push task mechanism for fair`：优化与 tick 联动、强制推走。
- 12/18 `Try to push short slice task on a better CPU`、13/18 `Push short slice task that are not picked`、14/18 `Enable push task for preempt short`：短 slice 任务的三种触发面（选到更差 CPU 时推、没被 pick 时推、被 preempt 时推）。

**EAS 侧重构（新增）**
- 16/18 `Rework feec() to use cost instead of spare capacity`：feec() 原来挑「spare capacity 最大的 CPU」（假设 OPP 增量最小）；重写为「先找 PD 内最低 OPP cost、再在等 cost 的 CPU 里挑最强算力」——很多 CPU 会落在同一个 OPP、能量成本相同，此时可用其它指标挑最优。`struct energy_env` 改为 per-CPU 的 `energy_cpu_stat`（idx/cost/max_perf/min_perf/capa/runnable/nr_running/fits/cpu）。kernel/sched/fair.c +250/−219。
- 18/18 `Take into account slice in EAS`：EAS 能量评估计入任务 slice。

对 Christian 10-01 提议的「选 `vprot - vruntime` 最小的 rq」维度，Vincent 回复：「We don't take any lock so can't use current->vprot or current->vruntime directly. I have merged select_slice_cpu() in select_idle_capacity and select_idle_cpu() in the next version that I just sent」——选 CPU 路径无锁，读不到 current 的 vprot/vruntime，故未采纳该维度。

## 版本演进与当前进展

- v1（09-21，8 补丁「Improving latency of short slice tasks」，对应 sched-20260921-001）：dragonboard rb5 数据（cyclictest 99.9 分位 +14%~+25%、hackbench pipe +11%~+30%）。
- 09-22 Peter 建议 8/8 复用初次扫描；09-27 Kayra 质疑 `nr_idle_scan`；09-29 Vincent 宣布合并进 idle CPU 搜索（sched-20260929-018）。
- 10-01：Christian 建议 vprot-vruntime 维度（sched-20261001-010）。
- 10-02（今天）：18 补丁 v2 发出（`<20261002154415.2270586-1-…>`）；Vincent 在 8/8 讨论线回复 Christian（`<CAKfTPtCh0+8YWsiSeKR3ZGMAz4b+u95jVAs4kNtKjcUBVnQpBQ@mail.gmail.com>`）说明无锁约束与合并结果。当日无人 review v2。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**（作者，fair 调度核心开发者）：主导扩张；明确拒绝 vprot-vruntime 维度的技术理由（无锁路径读不到 current 的 vprot/vruntime）。
- **Peter Zijlstra**（sched 维护者）：此前「与 select_idle_sibling() 重复」意见已通过合并落实；对 v2 本体当日无新表态。
- **Christian Loehle**（ARM）：vprot-vruntime 建议被拒（技术约束），其要求的「不同 slice 长度混合负载数据」尚无人提供。
- 潜在焦点：push task 机制与既有 `push_idle_task`/RT push 的关系、feec() 重构对非 EAS 平台的 noop 性、18 补丁一次合入的切分策略——均待评审暴露。

## 合入评估

*likelihood=medium*。v1 已有完整 benchmark 背书、Peter/Kayra/Christian 三方意见全部在 v2 落实或明确拒绝，方向成熟；但 v2 从 8 补丁翻倍到 18 补丁、新引入 push task 机制与 feec() 大改（+250/−219）两个架构级变更，评审量陡增，且当日零回帖。*blocking_issues*：v2 无任何 review；feec() cost 重构与 push task 机制两个大件需要 Peter/QLinux EAS 侧逐个消化；15/18、17/18 未进缓存、系列全貌未完全可见。*next_action*：等 Peter 对 v2 的第一轮结构性 review（尤其 07-14 push 机制组与 16/18 feec 重构）。

## 效果评估

v2 当日无新数据。v1 既有数据（09-21，dragonboard rb5，130s/组）：cyclictest（3777us 周期、8ms slice）99 分位 +1%、99.9 分位 +14%、最大延迟 +55%；cyclictest+rt-app 99.9 分位 +25%；cyclictest+hackbench 99.9 分位 +13%；hackbench pipe（默认 2.8ms slice）process 组 +11%~+25%、thread 组 +12%~+30%。16/18 feec 重构与 push 机制的效果数据尚未提供。

## 我可以参与的点

- `review`：审读 16/18 feec() 重构——「最低 cost → 等 cost 里挑最强 CPU」的两阶段选择在 PD 边界、capacity 不齐（异构）平台上的正确性，以及 `energy_cpu_stat` 各字段在 race 下的读序。
- `review`：核对 07/18 push task 机制与 RT 侧 `push_rt_tasks()` 的对称性（pushable_tasks plist 的锁序、`move_queued_task()` 导出后的调用方约束）。
- `testing`：构造 Christian 要求的「短/中/长 slice 混合 + 无空闲 CPU」负载测 v2 各分组（单独 bisect 01/02/18 vs 03-14 vs 16）的延迟分布。

## 参考链接

- v2 系列（05/18）: https://lore.kernel.org/all/20261002154415.2270586-6-vincent.guittot@linaro.org/
- v2 01/18（lag 衰减）: https://lore.kernel.org/all/20261002154415.2270586-2-vincent.guittot@linaro.org/
- v2 16/18（feec 重构）: https://lore.kernel.org/all/20261002154415.2270586-17-vincent.guittot@linaro.org/
- Vincent 回复 Christian: https://lore.kernel.org/all/CAKfTPtCh0+8YWsiSeKR3ZGMAz4b+u95jVAs4kNtKjcUBVnQpBQ@mail.gmail.com/
- v1 系列（09-21）: https://lore.kernel.org/all/20260921152238.3804392-9-vincent.guittot@linaro.org/

---
id: sched-20261002-001
date: '2026-10-02'
subject: 'sched/eevdf: Add min slice check when selecting CPU'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
lore_url: 'https://lore.kernel.org/all/20261002154415.2270586-6-vincent.guittot@linaro.org/'
authors:
  - 'Vincent Guittot'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20260921152238.3804392-9-vincent.guittot@linaro.org>'
    date: '2026-09-21'
    summary: '8 补丁「Improving latency of short slice tasks」：select_slice_cpu() min slice 检查等'
    review_outcome: 'Peter 建议复用初次扫描；Kayra 质疑 nr_idle_scan；Christian 建议 vprot-vruntime 维度'
  - version: v2
    msgid: '<20261002154415.2270586-1-vincent.guittot@linaro.org>'
    date: '2026-10-02'
    summary: '扩张为 18 补丁：lag 衰减/重置、per-cpu min_slice、select_slice_cpu 并入 idle 搜索、push task 机制、feec() cost 重构、EAS 计入 slice'
    review_outcome: '当日无 review；Christian 的 vprot-vruntime 建议因无锁约束被拒'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'v2 无任何 review'
    - 'push task 机制与 feec() 重构两个架构级变更需维护者消化'
    - '15/18、17/18 未进当日缓存'
  next_action: '等 Peter 对 v2 的第一轮结构性 review'
contribution_opportunities:
  - kind: review
    description: '审读 feec() cost 两阶段选择的异构平台正确性；核对 push task 与 RT push 的对称性'
  - kind: testing
    description: '短/中/长 slice 混合负载下 bisect v2 各分组的延迟分布'
generated_at: '2026-10-03T01:00:00'
source_email_count: 17
related_articles:
  - sched-20260921-001
  - sched-20260929-018
  - sched-20261001-010
tags:
  - eevdf
  - load_balance
  - eas
---
