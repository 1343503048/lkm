# sched_ext: Add scx_bpf_cgroup_nr_cpus()

> **subject**：`sched_ext: Add scx_bpf_cgroup_nr_cpus()`

## TL;DR

Andrea Righi（sched_ext 维护者）为 sched_ext/for-7.4 发的 3 补丁系列：层级式 BPF 调度器在分配 group-wide 权重时需要知道某个 cgroup 能在多少 CPU 上运行，新 kfunc `scx_bpf_cgroup_nr_cpus()` 直接返回与 fair 的 `cpuset_num_cpus()` 相同的计数（cgroup 有效 cpuset 的 CPU 数），避免 BPF 只能拿全机 CPU 数、给被 cpuset 限制到少数核的 group 过高份额。附带兼容包装（旧内核回退 `nr_cpu_ids`）与 selftest。

## 背景与问题

层级式 BPF 调度器在按 group 分配权重时，需要知道某 cgroup 能跑在多少 CPU 上。fair 的 group share 计算会按「估算可运行任务数与有效 cpuset CPU 数的较小者」缩放 group 权重（`tg_cpus()` → `cpuset_num_cpus()`）；没有这个计数，BPF 调度器只能用全机 CPU 数，可能给被 cpuset 限制到少数核的 group 过高份额。任务的有效亲和性含 per-task 限制，不能可靠代表 group 的 cpuset；而 BPF 直接读 cpuset 需要 CO-RE 访问私有 cgroup/cpuset 结构（含继承解析），跨内核版本脆弱。

## 技术方案

三片补丁：

1. **`cgroup/cpuset: Protect is_in_v2_mode() in cpuset_num_cpus()`**（未进入缓存，据 cover）：保护 `cpuset_num_cpus()` 里的 `is_in_v2_mode()`。
2. **`sched_ext: Introduce scx_bpf_cgroup_nr_cpus()`**：新增 `__bpf_kfunc u32 scx_bpf_cgroup_nr_cpus(struct cgroup *cgrp)`，返回 `cpuset_num_cpus(cgrp)`（cgroup 有效 cpuset 的 CPU 数，继承自最近启用 cpuset controller 的祖先）。计数与 CPU/CID 编号无关，因此 cpu-form 与 cid-form 调度器在任何上下文都可用；cgroup v1 无 `cpuset_v2_mode`、或未配 cpuset 时返回在线 CPU 数；无有效 CPU 的 partition root 可能返回 0。BTF 注册带 `KF_RCU`。附 `compat.bpf.h` 的兼容包装，旧内核回退 `nr_cpu_ids`。
3. **`selftests/sched_ext: Test scx_bpf_cgroup_nr_cpus()`**：新建 cgroup-v2 子树（子拥有 cpuset、叶继承），用 `BPF_PROG_TYPE_SYSCALL` 程序采样 kfunc 并与 `cpuset.cpus.effective` 对比；验证 `ops.cgroup_init()` 里观测到的值；再限制子 cpuset 到非连续/单 CPU 集，最后 disable cpuset 使两级继承父 cpuset。带 `Assisted-by: LLM`。

## 版本演进与当前进展

v1 刚发出（PATCHSET cover `<20260929084124.626693-1-arighi@nvidia.com>`，含 1/3、2/3、3/3；其中 1/3 未进入当日缓存）。当日无回帖。

## Maintainer 意见与讨论焦点

当日无回帖。作者即 sched_ext 维护者（Andrea Righi），系列自投 `sched_ext/for-7.4`，待 Tejun Heo 审阅/收取。

## 合入评估

*likelihood=high*。作者是 sched_ext 维护者本人、系列自含 kernel 实现 + compat 包装 + selftest、语义直接复用 fair 的 `cpuset_num_cpus()`（低风险），目标是自家 for-7.4 分支。*blocking_issues*：尚未见 Tejun Heo 的审阅/收取；1/3 未在缓存中。*next_action*：等 Tejun 审阅后应用进 sched_ext/for-7.4。

## 效果评估

无性能数据；属调度器编程接口能力补充，效果体现在让层级式 BPF 调度器能按 cgroup 真实 CPU 数约束权重，邮件未附量化对比。

## 我可以参与的点

- `review`：核对 `scx_bpf_cgroup_nr_cpus()` 的 `KF_RCU` 与 `cpuset_num_cpus()` 调用是否满足 kfunc 上下文/生命周期约束，以及 cgroup v1 无 v2_mode 时的回退语义。
- `testing`：在 cgroup v1/v2 两种模式下用 scx 示例调度器验证返回的 CPU 数与 `cpuset.cpus.effective` 一致（含 partition root、热插拔场景）。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20260929084124.626693-1-arighi@nvidia.com/
- lore（2/3）: https://lore.kernel.org/all/20260929084124.626693-3-arighi@nvidia.com/

---
id: sched-20260929-011
date: '2026-09-29'
subject: 'sched_ext: Add scx_bpf_cgroup_nr_cpus()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20260929084124.626693-1-arighi@nvidia.com>'
lore_url: 'https://lore.kernel.org/all/20260929084124.626693-1-arighi@nvidia.com/'
authors:
  - 'Andrea Righi'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260929084124.626693-1-arighi@nvidia.com>'
    date: '2026-09-29'
    summary: '新增 scx_bpf_cgroup_nr_cpus() kfunc（返回 cpuset_num_cpus）+ compat 包装 + selftest'
    review_outcome: '无回帖'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '尚未见 Tejun 审阅/收取'
  next_action: '等 Tejun 审阅后应用进 sched_ext/for-7.4'
contribution_opportunities:
  - kind: review
    description: '核对 kfunc KF_RCU 与 cpuset_num_cpus 调用的生命周期约束及 v1 无 v2_mode 回退语义'
  - kind: testing
    description: '在 cgroup v1/v2 下验证返回 CPU 数与 cpuset.cpus.effective 一致（含 partition root/热插拔）'
generated_at: '2026-09-30T01:15:00'
source_email_count: 3
related_articles: []
tags:
  - sched_ext
  - cgroup
---