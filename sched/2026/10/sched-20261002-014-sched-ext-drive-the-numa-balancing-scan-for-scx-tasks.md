# sched_ext: Drive the NUMA balancing scan for SCX tasks

> **subject**：`sched_ext: Drive the NUMA balancing scan for SCX tasks`

## TL;DR

Vladimir Vdovin 的单片 RFC：自动 NUMA balancing 对 sched_ext 任务**事实性关闭**——周期性扫描只从 fair tick（`task_tick_fair()` → `task_tick_numa()`）排队，`task_tick_scx()` 没有对应调用，SCX 任务永不产生 PROT_NONE PTE、fault 侧无活可干。2 节点 160-CPU KVM 宿主机实测：SCX 下 `numa_pte_updates/s = 0`（fair 为 2.4M-3.9M）、任务跑在 preferred nid 的比例 37%（fair 跑 5 分钟后 83%）、58% 任务根本没有 preferred_nid。补丁从 `task_tick_scx()` 调 `task_tick_numa()`（非 static 化），但跳过 SCX 任务的 `task_numa_migrate()` CPU 选择（归 BPF 调度器）。Andrea Righi（sched_ext 维护者）回复：自己 backlog 里正有一套 sched_ext NUMA balancing 支持（opt-in 扫描 + preferred node 暴露给 BPF + per-task 内存目标），下周 LPC Prague sched_ext MC 会讨论，将尽快发到列表；Vladimir 当场表示放弃自己的 sketch 转而跟进 Andrea 的系列，并主动提供 2/4 节点宿主机测试。

## 背景与问题

NUMA balancing 的周期扫描（`task_numa_work()` 做 PROT_NONE 标记）由 `task_tick_fair()` 触发；fault 侧（`task_numa_fault()` 记账、`task_numa_placement()` 迁移 folio）与调度类无关。sched_ext 任务挂在 ext 类，tick 走 `task_tick_scx()`——没有 NUMA 扫描触发点。后果链条：

- 无扫描 → 无 PROT_NONE PTE → 无 hint fault → `numa_preferred_nid` 停留在上次 fair 时期的值；BPF 调度器加载期间新建的任务则从未有过 preferred_nid；
- BPF 调度器想「把 vCPU 线程放在其内存所在节点」时读 `p->numa_preferred_nid`，读到的是陈旧或空值；
- 宿主机场景（Vladimir 的用例）：vCPU 线程的 home node 选择依赖 preferred_nid 的多数投票，SCX 下该值冻结。

实测数据（6.18.5、2 节点 160-CPU KVM 宿主机、BPF 调度器 attach/detach/attach）：

```
                     SCX      fair (5 min)   SCX again
numa_pte_updates/s    0        2.4M - 3.9M    0
numa_hint_faults/s   ~0        10K - 34K      200-300, decaying
```

fair 跑 5 分钟前后的 BPF 侧观测（任务运行时占比）：无 preferred_nid 58%→10%；跑在 preferred_nid 上 37%→83%。

## 技术方案

补丁（`<20261002124559.10367-1-deliran@verdict.gg>`，3 文件 +17/−5，RFC 且**未 build/run**——数字来自未打补丁的 6.18.5 只证问题）：

- `task_tick_scx()` 里 `if (!queued && static_branch_unlikely(&sched_numa_balancing)) task_tick_numa(rq, curr);`（只需 `p->se.sum_exec_runtime`，SCX 经 `update_curr_common()` 维护）。
- `numa_migrate_preferred()` 对 `task_on_scx(p)` 直接返回：`task_numa_migrate()` 用 fair 负载统计选 CPU，对 SCX 任务无意义且 CPU 选择权属 BPF 调度器；扫描、fault 记账、preferred_nid、folio 迁移保持工作。
- `task_tick_numa()` 从 static 改为 extern（含 !CONFIG_NUMA_BALANCING 的空 stub）。

作者附四个开放问题：扫描缺失是否有意；从 ext tick 调 fair.c 函数是否可接受（是否应等 proxy execution tick 系列定稿）；跳过 `task_numa_migrate()` 的切分对不对、要不要 ops 回调让 BPF 参与；是否应做成 opt-in 的 ops flag。

**Andrea 的替代方向**（回复 `<ar--fEmqMyX8odNn@gpd4>`）：其 backlog 系列把 NUMA hinting 扫描做成 BPF 调度器 opt-in、暴露任务的 preferred NUMA node 给 BPF，并允许 BPF 为任务设置内存目标（hinting fault 后的页面迁移按该目标走）——「give schedulers a useful way to coordinate CPU and memory placement, including when device locality constrains CPU choice」。LPC'26 Prague sched_ext MC 有专场讨论；「I can probably send the patch series at this point, it's not completely well-tested, but it might be useful to have it on the list」。

## 版本演进与当前进展

- RFC v1（10-02）发出；Andrea 当日回复预告自己的系列；Vladimir 回复（`<DLUG3Q30BQDS.1WMLGJKNHOYPV@verdict.gg>`）：「My patch was only a small sketch to show the problem, so I am happy to leave it at that and follow your series instead」，并补了用例细节（vCPU home node 用 preferred_nid 多数投票、双节点 guest 是难点——「today I can only follow the memory, I cannot ask for it to follow the vCPUs」）与测试要约（2/4 节点宿主机上测 scan rate、hint faults、preferred node 占比）。
- RFC 未 build 未跑（作者明说想先对齐方向）。

## Maintainer 意见与讨论焦点

- **Andrea Righi**（NVIDIA，sched_ext 维护者）：确认问题真实（「Thanks for looking at this!」）、宣布自己有覆盖面更广的方案在路上（opt-in + BPF 可写内存目标），指向 LPC 讨论。实质上是「方向认可、实现将由我的系列承担」。
- **Vladimir Vdovin**（作者）：让位给 Andrea 的系列，转为测试者角色。
- 焦点：Vladimir 的「无差别 tick 扫描 + 跳过 migrate」 vs Andrea 的「opt-in + BPF 主导内存目标」——后者与 sched_ext 的 BPF 自主哲学一致，大概率胜出。

## 合入评估

*likelihood=low*（本 RFC 本体）。维护者已预告功能更完整的替代系列、作者本人也转向跟进；本 RFC 的价值在于把问题与实测数据钉在列表上，为 Andrea 的系列提供动机背书。*blocking_issues*：被 Andrea 的系列实质取代（未发出）；RFC 未 build 未测。*next_action*：跟踪 Andrea 系列（LPC 后应很快上列表）；Vladimir 的实测数据会被复用为该系列的动机材料。

## 效果评估

问题侧数据完备（见上：pte_updates 0 vs 2.4M-3.9M/s、preferred_nid 占比 37% vs 83%、58% 无 preferred_nid）；方案侧零数据（补丁未 build）。

## 我可以参与的点

- `testing`：Andrea 的系列发出后（或 LPC 材料出现后），在多节点机器上复测「SCX 任务 preferred_nid 覆盖率 + pte_updates」基线，与 Vladimir 的数字互证。
- `review`：如果 Andrea 的系列采用 opt-in ops flag，评估默认关闭时 fair↔SCX 切换期的 preferred_nid 陈旧问题是否仍需兜底（Vladimir RFC 的最小修补可作为 fallback 讨论）。

## 参考链接

- Vladimir 的 RFC: https://lore.kernel.org/all/20261002124559.10367-1-deliran@verdict.gg/
- Andrea 的回复（预告系列+LPC）: https://lore.kernel.org/all/ar--fEmqMyX8odNn@gpd4/
- Vladimir 的让位+测试要约: https://lore.kernel.org/all/DLUG3Q30BQDS.1WMLGJKNHOYPV@verdict.gg/

---
id: sched-20261002-014
date: '2026-10-02'
subject: 'sched_ext: Drive the NUMA balancing scan for SCX tasks'
subsystem: sched
type: feature
status: rfc
severity: medium
thread_root_msgid: '<20261002124559.10367-1-deliran@verdict.gg>'
lore_url: 'https://lore.kernel.org/all/20261002124559.10367-1-deliran@verdict.gg/'
authors:
  - 'Vladimir Vdovin'
maintainers_involved:
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261002124559.10367-1-deliran@verdict.gg>'
    date: '2026-10-02'
    summary: 'task_tick_scx() 驱动 task_tick_numa()，跳过 SCX 的 task_numa_migrate()'
    review_outcome: 'Andrea 预告自己的 opt-in 系列；作者让位转测试角色'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '被 Andrea 的替代系列实质取代（未发出）'
    - 'RFC 未 build 未测'
  next_action: '跟踪 Andrea 系列（LPC 后上列表）'
contribution_opportunities:
  - kind: testing
    description: '多节点机器复测 preferred_nid 覆盖率基线与 Vladimir 数字互证'
  - kind: review
    description: '评估 opt-in 默认关闭时 fair↔SCX 切换期 preferred_nid 陈旧的兜底'
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles: []
tags:
  - sched_ext
  - numa
---
