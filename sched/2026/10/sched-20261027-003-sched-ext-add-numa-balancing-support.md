# sched_ext: Add NUMA balancing support

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261002-014：Vladimir Vdovin 的单片 RFC——自动 NUMA balancing 对 sched_ext 任务事实性关闭：扫描只从 fair tick 排队，SCX 任务 `numa_pte_updates/s = 0`、跑在 preferred nid 比例 37%（fair 83%）。Andrea 回复正有一整套 sched_ext NUMA balancing 支持跟进。
- sched-20261004-001（v1）：Andrea 兑现承诺，发出 5 补丁系列：`SCX_OPS_NUMA_BALANCING` opt-in 让 BPF 调度器为任务请求 NUMA hinting-fault 扫描，扫描从 sched_ext tick 驱动。
- sched-20261027-003（今天，v2）：扩到 6 补丁，按 Tejun 意见用 `ops.set_numa_node()` 回调取代 flag；Peter Zijlstra 上线深度 review 并提出架构性异议（「不该是 BPF 层的东西」「应先清理再加新东西」「建议用 `p->class->task_numa_migrate()`」），方向仍在博弈。

## 背景与问题
（承接 20261004-001）BPF 调度器下的任务对 NUMA balancing 不可见：地址空间从不被扫描 hinting fault，NUMA fault 统计与 preferred node 永远为空——BPF 调度器决定任务放哪时拿不到「任务的内存在哪」的信息。Vladimir 的 KVM 宿主机实测（2 节点 160 CPU）：SCX 下 `numa_pte_updates/s = 0`、58% 任务无 preferred_nid、跑在 preferred nid 37% vs fair 83%。v2 的增量：系列目标从 for-7.4 顺延到 for-7.5，并回应 Peter 在 LPC 2026 scx microconference 与 OSPM 的关切，把接口从一次性 flag 收敛为「回调即 opt-in」。

## 技术方案
v2 共 6 补丁（`kernel/sched/*` + tools/sched_ext + selftests，9 files +527/−7）：

1. **sched/numa: Let other scheduling classes drive NUMA scanning**：通用 NUMA 代码小改动，把扫描开放给 fair 之外的调度类。
2. **sched/numa: Leave the placement of a BPF-scheduled task to its scheduler**：跳过 fair 类任务迁移路径（BPF 调度器负责任务放置），也绝不把 BPF 任务选为公平任务 NUMA 迁移的 swap partner；不改 fair/RT/DL 行为。
3. **sched/numa: Notify the scheduling class of preferred node changes**：新增可选 `sched_class->numa_node_changed()` 方法（目前仅 sched_ext 实现），使 sched core 不含类专有代码。
4. **sched_ext: Report preferred NUMA nodes through ops.set_numa_node()**：新回调取代 v1 的 `SCX_OPS_NUMA_BALANCING` flag；实现该回调即启用 hinting-fault 扫描，preferred node 变化由 `sched_setnuma()` 在 rq lock 下、re-enqueue 前上报。
5. **sched_ext: Add a kfunc to read a task's preferred NUMA node**：`scx_bpf_task_numa_nid()` 供调度器在任意回调读取当前偏好；对未实现回调的调度器返回 `NUMA_NO_NODE`。
6. **selftests/sched_ext: Test preferred NUMA node notifications**：`numa_nid` 自测验证 enable 时初始通知、变化去重、与 kfunc 返回值一致性。

v2 关键变化：flag → 回调（Tejun Heo）；扫描改从 donor 驱动以对齐 `task_tick_fair()`（Vladimir Vdovin）；绝不选 BPF 任务作 swap partner。

## 版本演进与当前进展
*current_version: v2*（`<20261027041536.3317971-1-arighi@nvidia.com>`）。v1（2026-10-04，5 patches，for-7.4）→ v2（2026-10-27，6 patches，for-7.5）。今日 Peter Zijlstra、K Prateek Nayak 密集 review，Andrea 已逐条回应。

## Maintainer 意见与讨论焦点
Peter Zijlstra 今日语出重评，方向性异议为主：
- 「This really should not be a bpf thing」——认为「regular numa balancing 也想要这个」，不该做成 scx 专有。
- 「Should not we cleanup first and then add shiny on top?」——先清理公平侧再叠加新接口。
- 建议用 `p->class->task_numa_migrate(p)` 类回调而非在 `sched_setnuma()` 里塞回调，并质疑「为何 sched_ext 需要 sched_setnuma() 这个 hint」；「RT/DL should definitely be ignored」。
- 质疑 `set_numa_node()` 在 enable 时的额外调用（「The signal was sched_setnuma(), but now you're doing more」）。
- 对后续要给的「BPF 控制内存迁移」kfunc 直接问「Fair 也没有这个控制，为何要给 BPF」（202277）。

K Prateek Nayak：认可「不打扰可抢占 CPU 若周围有更好选择/空闲 CPU」；追问 NA balancing 运行时关闭时 `scx_bpf_task_numa_nid()` 是否返回 stale 值、`scx_bpf_task_running()` 是否真需 `KF_RCU`。Andrea 回应会加准备补丁把公平侧两处 `numa_preferred_nid` 使用也 gate 到 `sched_numa_balancing`、并使 kfunc 在关闭时返回 `NUMA_NO_NODE`。

## 合入评估
*likelihood=medium*。方向获社区持续关注（LPC/OSPM 都讨论过），但 Peter 的架构性异议（应通用化、应先清理、类回调 vs 回调）需要 Andrea 在下一版回应，短期内不会直接合入。*blocking_issues*：接口形态未定（类方法 vs scx 回调/kfunc）、通用 NUMA 清理前置。*next_action*：Andrea 按 Peter 意见重做接口、补准备补丁后发 v3。

## 效果评估
无本版新 benchmark。背景引用 Vladimir 实测：SCX `numa_pte_updates/s = 0`、跑在 preferred nid 37% vs fair 83%（主观动机数据，来自 v1 前的研究）。

## 我可以参与的点
- *kind: review*：对「类回调 `p->class->task_numa_migrate()` vs `sched_setnuma()` 回调」两种接口形态给出判断，是当前争议核心。
- *kind: testing*：在多 NUMA 节点机器上跑 `numa_nid` selftest 或用真实 BPF 调度器验证 preferred node 变化通知的时序。

## 参考链接
- v2 cover: https://lore.kernel.org/all/20261027041536.3317971-1-arighi@nvidia.com/
- v1: https://lore.kernel.org/r/20261004072901.3579967-1-arighi@nvidia.com
- Vladimir RFC: https://lore.kernel.org/r/20261002124559.10367-1-deliran@verdict.gg

---
id: sched-20261027-003
date: 2026-10-27
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261027041536.3317971-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20261027041536.3317971-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261004072901.3579967-1-arighi@nvidia.com>'
    date: 2026-10-04
    summary: '5 patches，SCX_OPS_NUMA_BALANCING flag opt-in + sched_ext tick 驱动扫描'
    review_outcome: 'Tejun/Vladimir 反馈后重做'
  - version: v2
    msgid: '<20261027041536.3317971-1-arighi@nvidia.com>'
    date: 2026-10-27
    summary: '6 patches，用 ops.set_numa_node() 回调取代 flag，加 kfunc 与 selftest；Peter 提架构异议'
    review_outcome: 'Peter 深度 review，方向待定'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - '接口形态未定：类方法 vs scx 回调/kfunc'
    - '通用 NUMA 清理前置工作尚未完成'
  next_action: 'Andrea 按 Peter 意见重做接口并补准备补丁后发 v3'
contribution_opportunities:
  - kind: review
    description: '判断「类回调 task_numa_migrate()」与「sched_setnuma() 回调」两种接口形态的取舍'
  - kind: testing
    description: '多 NUMA 节点机器上验证 preferred node 变化通知时序'
generated_at: '2026-10-28T09:00:00'
source_email_count: 18
related_articles:
  - sched-20261004-001
tags:
  - sched_ext
  - numa_balancing
---