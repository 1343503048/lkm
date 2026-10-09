# sched_ext: Add NUMA balancing support

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261002-014：Vladimir Vdovin 的单片 RFC——自动 NUMA balancing 对 sched_ext 任务**事实性关闭**：扫描只从 fair tick 排队，SCX 任务 `numa_pte_updates/s = 0`（fair 2.4M-3.9M）、跑在 preferred nid 比例 37%（fair 83%）。Andrea Righi（sched_ext 维护者）回复 backlog 里正有一套 sched_ext NUMA balancing 支持（opt-in 扫描 + preferred node 暴露 + per-task 内存目标），将发到列表；Vladimir 当场撤下自己的 sketch 转做测试员。
- sched-20261004-001（今天）：**Andrea 兑现承诺，发出 5 补丁系列**（`[PATCHSET sched_ext/for-7.4]`）：`SCX_OPS_NUMA_BALANCING` opt-in 让 BPF 调度器为任务请求 NUMA hinting-fault 扫描，扫描从 sched_ext tick 驱动（与 `task_tick_fair()` 同构），fault 记账/preferred node/内存迁移照常工作、但任务放置留给 BPF 调度器；`scx_bpf_task_numa_nid()` 把 preferred node 暴露给 BPF（advisory）；3/5 带 `Reported-by: Vladimir Vdovin`——确认覆盖其 RFC 全部内容并叠加 opt-in flag 与 kfunc。第二个系列（内存侧 kfunc，让 BPF 提示内存管理器迁移任务内存）待本系列落地后跟进。

## 背景与问题

（承接 sched-20261002-014）BPF 调度器下的任务对 NUMA balancing 不可见：地址空间从不被扫描 hinting fault，NUMA fault 统计与 preferred node 永远为空——BPF 调度器决定任务放哪时拿不到「任务的内存在哪」的信息。Vladimir 的 KVM 宿主机实测（2 节点 160 CPU）：SCX 下 `numa_pte_updates/s = 0`、58% 任务无 preferred_nid、跑在 preferred nid 37% vs fair 83%。

## 技术方案

5 补丁（`<20261004072901.3579967-{1..6}-arighi@nvidia.com>`，11 文件 +246/−7，git tree `scx-numa-balancing`）：

1. **sched/numa: Let other scheduling classes drive NUMA scanning**：通用 NUMA 代码小改动，把扫描开放给 fair 之外的调度类。
2. **sched/numa: Leave the placement of a BPF-scheduled task to its scheduler**：跳过 fair 类任务迁移路径（BPF 调度器负责任务放置）；不改 fair/RT/DL 行为。
3. **sched_ext: Scan NUMA hinting faults for opted-in BPF schedulers**：`SCX_OPS_NUMA_BALANCING` flag；从 sched_ext tick 驱动扫描（`task_tick_numa()` 空间节奏用 `p->se.sum_exec_runtime`，SCX 经 `update_curr_common()` 已维护）；hrtick（只切 slice）不驱动扫描，与 fair 一致。`Reported-by: Vladimir Vdovin`。
4. **sched_ext: Add scx_bpf_task_numa_nid()**：kfunc 暴露 preferred node，advisory 性质（内核不据此动作）。
5. **selftests/sched_ext: Add a test for scx_bpf_task_numa_nid()**：numa_nid.bpf.c + numa_nid.c 自测。

目标分层明确：本系列只给「把任务移到内存所在节点」的控制（placement 归 BPF）；后续系列再给「把内存移到任务所在节点」的 kfunc。BPF 侧兼容头（compat.bpf.h/compat.h）同步更新。

## 版本演进与当前进展

- Vladimir RFC（10-02，`<20261002124559.10367-1-deliran@verdict.gg>`）：单片 sketch，未 build/run。
- 本系列 v1（10-04，`<20261004072901.3579967-1-arighi@nvidia.com>`）：覆盖 RFC 内容 + opt-in + kfunc + selftest；发往 `sched_ext/for-7.4`。

## Maintainer 意见与讨论焦点

- 无回帖（发布当日）。Andrea 自身是 sched_ext 维护者、目标分支即其 for-7.4，Tejun 的 review 是事实关口。
- 与 Vladimir RFC 的关系已在 cover 澄清（覆盖 + 增强，Reported-by 致谢）。

## 合入评估

*likelihood=medium*。作者即分支维护者、方案与 LPC 讨论方向一致、有 selftest 与外部触发者实测背景；但 NUMA 代码改动会 CC Mel Gorman/Peter 等公平侧维护者（patch 1-2 动 kernel/sched/fair.c 与 sched.h），跨子域 review 周期难料，且「第二个系列」的内存侧 kfunc 依赖本系列先行。*blocking_issues*：Tejun 与 NUMA 侧维护者 review 未开始。*next_action*：等 Tejun/Mel 侧 review；Vladimir 已承诺提供 2/4 节点宿主机测试。

## 效果评估

系列无自带 benchmark（selftest 验证 kfunc 语义）。问题严重度与可行性数据承接 Vladimir RFC 的实测（`numa_pte_updates/s = 0` vs 2.4M-3.9M、preferred nid 37% vs 83%）。合入后的收益量化待 Vladimir 的宿主机复测。

## 我可以参与的点

- `testing`：在多节点机器上用 `SCX_OPS_NUMA_BALANCING` 调度器（如 llama.rs 类用户态调度器）复测 Vladimir 的指标（numa_pte_updates/s、preferred nid 命中率），给系列补 before/after 数据。
- `review`：评审 patch 1-2 对 fair/RT/DL 行为零影响的论证（cover 声称，值得独立核对切换路径）。

## 参考链接

- lore（系列 cover）: https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/
- lore（3/5 扫描补丁）: https://lore.kernel.org/all/20261004072901.3579967-4-arighi@nvidia.com/
- lore（Vladimir RFC）: https://lore.kernel.org/all/20261002124559.10367-1-deliran@verdict.gg/

---
id: sched-20261004-001
date: '2026-10-04'
subject: 'sched_ext: Add NUMA balancing support'
subsystem: sched_ext
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261004072901.3579967-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20261004072901.3579967-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Andrea Righi'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261004072901.3579967-1-arighi@nvidia.com>'
    date: '2026-10-04'
    summary: '5 补丁：SCX_OPS_NUMA_BALANCING opt-in 扫描 + scx_bpf_task_numa_nid() kfunc + selftest'
    review_outcome: '发布当日无回帖；覆盖 Vladimir RFC 并致谢'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Tejun 与 NUMA 侧维护者 review 未开始'
  next_action: '等 review；Vladimir 承诺宿主机复测'
contribution_opportunities:
  - kind: testing
    description: '多节点机器上用 opt-in 调度器复测 numa_pte_updates 与 preferred nid 命中率'
  - kind: review
    description: '核对 patch 1-2 对 fair/RT/DL 行为零影响的论证'
generated_at: '2026-10-05T01:00:00'
source_email_count: 6
related_articles:
  - sched-20261002-014
tags:
  - sched_ext
  - numa
  - bpf
---
