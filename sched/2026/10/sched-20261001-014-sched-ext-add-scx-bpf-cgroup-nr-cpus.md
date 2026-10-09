# sched_ext: Add scx_bpf_cgroup_nr_cpus()

> **subject**：`sched_ext: Add scx_bpf_cgroup_nr_cpus()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260929-011：Andrea Righi（sched_ext 维护者）为 sched_ext/for-7.4 发的 3 补丁系列，新增 kfunc `scx_bpf_cgroup_nr_cpus()` 直接返回与 fair `cpuset_num_cpus()` 相同的计数（cgroup 有效 cpuset 的 CPU 数），让层级式 BPF 调度器按 cgroup 真实 CPU 数分配 group 权重。
- sched-20260930-005：作者发 v2——drop 掉保护 `is_in_v2_mode()` 的 cpuset 前置补丁、改为依赖 Waiman Long 独立的 cpuset 修复，系列收敛为 2 补丁（kfunc + selftest）。
- sched-20261001-014（今天）：Tejun Heo 回帖「Applied 1-2 to sched_ext/for-7.4.」——v2 两片收取完成。

## 背景与问题

（承接 sched-20260930-005）层级式 BPF 调度器按 group 分配权重时需要知道某 cgroup 能跑在多少 CPU 上；fair 的 group share 计算按「可运行任务数与有效 cpuset CPU 数的较小者」缩放（`tg_cpus()` → `cpuset_num_cpus()`），没有这个计数 BPF 调度器只能用全机 CPU 数，可能给被 cpuset 限制到少数核的 group 过高份额。任务的有效亲和性含 per-task 限制、不能可靠代表 group 的 cpuset；BPF 直接读 cpuset 需要 CO-RE 访问私有 cgroup/cpuset 结构，跨内核版本脆弱。今天无新背景，事件是收取落地。

## 技术方案

（承接）v2 两片：1/2 新增 `__bpf_kfunc u32 scx_bpf_cgroup_nr_cpus(struct cgroup *cgrp)`，返回 `cpuset_num_cpus(cgrp)`，计数与 CPU/CID 编号无关、cpu-form 与 cid-form 调度器在任何上下文可用，附 `compat.bpf.h` 兼容包装（旧内核回退 `nr_cpu_ids`）；2/2 selftest 用 cgroup-v2 子树与 `BPF_PROG_TYPE_SYSCALL` 程序采样 kfunc 与 `cpuset.cpus.effective` 对比，覆盖有效/继承 cpuset、允许 CPU 变更、有无挂调度器，最后 disable cpuset 使两级继承父。今天无代码变更。

## 版本演进与当前进展

- v1（09-29，`<20260929084124.626693-1-arighi@nvidia.com>`）：3 补丁（cpuset 保护 + kfunc + selftest）。
- v2（09-30，`<20260930090049.1035813-1-arighi@nvidia.com>`）：2 补丁，依赖 Waiman Long 的 cpuset 修复。
- 10-01：Tejun 应用 1-2 到 `sched_ext/for-7.4`（`<fab12a20719cfc85160709675e7af5cc@kernel.org>`）。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 顶层维护者）：「Applied 1-2 to sched_ext/for-7.4. Thanks.」——收取完成，无附加意见。
- **Andrea Righi**（sched_ext 维护者、作者本人）：v2 按评审意见精简后获收取。
- 无 NAK、无未决争议；v2 依赖的 Waiman Long cpuset 修复的合入状态未在本日缓存中体现。

## 合入评估

*likelihood=merged*。维护者本人的系列（kfunc + compat + selftest、语义复用 fair 的 `cpuset_num_cpus()`）被 Tejun 全量收取进 `sched_ext/for-7.4`，随 v7.4 合入窗口进主线。*blocking_issues*：无（上游收取完成）。*next_action*：跟踪 for-7.4 进主线；若 Waiman Long 的 cpuset 修复尚未先行合入，注意 v2 的依赖在主线里的落地顺序。

## 效果评估

本日无新数据；属调度器编程接口能力补充，效果体现在让层级式 BPF 调度器（如 scx_eevdf）能按 cgroup 真实 CPU 数约束权重，未见量化对比。

## 我可以参与的点

- `testing`：在 cgroup v1/v2 两种模式下用 scx 示例调度器验证 kfunc 返回值与 `cpuset.cpus.effective` 一致（含 partition root、热插拔场景）——收取后的实测反馈仍有价值，尤其 v1 里被 drop 的 cpuset 路径。

## 参考链接

- Tejun 的收取通告: https://lore.kernel.org/all/fab12a20719cfc85160709675e7af5cc@kernel.org/
- v2 cover: https://lore.kernel.org/all/20260930090049.1035813-1-arighi@nvidia.com/
- Waiman 的 cpuset 修复: https://lore.kernel.org/r/20260930031833.660267-1-longman@redhat.com/

---
id: sched-20261001-014
date: '2026-10-01'
subject: 'sched_ext: Add scx_bpf_cgroup_nr_cpus()'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: '<20260930090049.1035813-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/fab12a20719cfc85160709675e7af5cc@kernel.org/'
authors:
  - 'Andrea Righi'
maintainers_involved:
  - 'Tejun Heo'
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260930090049.1035813-1-arighi@nvidia.com>'
    date: '2026-09-30'
    summary: 'kfunc scx_bpf_cgroup_nr_cpus() + selftest，依赖 Waiman Long 的 cpuset 修复'
    review_outcome: '10-01 Tejun 应用 1-2 进 sched_ext/for-7.4'
upstream_commit: null
fixes_commit: null
merged_branch: 'sched_ext/for-7.4'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '跟踪 for-7.4 进主线及 Waiman cpuset 修复的落地顺序'
contribution_opportunities:
  - kind: testing
    description: '在 cgroup v1/v2 下验证 kfunc 返回值与 cpuset.cpus.effective 一致（含 partition root、热插拔）'
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles:
  - sched-20260929-011
  - sched-20260930-005
tags:
  - sched_ext
---
