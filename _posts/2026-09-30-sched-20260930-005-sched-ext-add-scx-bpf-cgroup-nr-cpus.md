---
id: sched-20260930-005
date: '2026-09-30'
subject: 'sched_ext: Add scx_bpf_cgroup_nr_cpus()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260930090049.1035813-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260930090049.1035813-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved: []
current_version: v2
patch_series:
- version: v1
  msgid: <20260929084124.626693-1-arighi@nvidia.com>
  date: '2026-09-29'
  summary: 3 补丁：cpuset 保护 + 新增 scx_bpf_cgroup_nr_cpus() kfunc + selftest
  review_outcome: 无回帖
- version: v2
  msgid: <20260930090049.1035813-1-arighi@nvidia.com>
  date: '2026-09-30'
  summary: drop cpuset RCU guard 补丁，改为依赖 Waiman Long 的 cpuset 修复；2 补丁
  review_outcome: 无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 尚未见 Tejun 审阅/收取
  - 依赖 Waiman Long 的 cpuset 修复先行合入
  next_action: 等 Tejun 审阅、Waiman 的 cpuset 修复落地后应用进 sched_ext/for-7.4
contribution_opportunities:
- kind: review
  description: 核对 kfunc KF_RCU 与 cpuset_num_cpus 调用的生命周期约束及 v1 无 v2_mode 回退语义
- kind: testing
  description: 在 cgroup v1/v2 下验证返回 CPU 数与 cpuset.cpus.effective 一致（含 partition root/热插拔）
generated_at: '2026-10-01T01:00:00'
source_email_count: 3
related_articles:
- sched-20260929-011
tags:
- sched_ext
- cgroup
title: 'sched_ext: Add scx_bpf_cgroup_nr_cpus()'
layout: article
---

> **subject**：`sched_ext: Add scx_bpf_cgroup_nr_cpus()`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-011-sched-ext-add-scx-bpf-cgroup-nr-cpus.html">sched-20260929-011</a>：Andrea Righi（sched_ext 维护者）为 sched_ext/for-7.4 发的 3 补丁系列，新增 kfunc `scx_bpf_cgroup_nr_cpus()` 直接返回与 fair `cpuset_num_cpus()` 相同的计数（cgroup 有效 cpuset 的 CPU 数），让层级式 BPF 调度器按 cgroup 真实 CPU 数分配 group 权重；附 compat 包装与 selftest。
- <a class="article-ref" href="/lkm/2026/09/30/sched-20260930-005-sched-ext-add-scx-bpf-cgroup-nr-cpus.html">sched-20260930-005</a>（今天）：作者发 v2——按 v1 反馈 drop 掉 `cgroup/cpuset: Protect is_in_v2_mode()` 这一片，改为依赖 Waiman Long 独立的 cpuset 修复（`20260930031833.660267-1-longman@redhat.com`），系列从 3 补丁收敛为 2 补丁（kfunc + selftest）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-011-sched-ext-add-scx-bpf-cgroup-nr-cpus.html">sched-20260929-011</a>）层级式 BPF 调度器在按 group 分配权重时，需要知道某 cgroup 能跑在多少 CPU 上。fair 的 group share 计算按「估算可运行任务数与有效 cpuset CPU 数的较小者」缩放 group 权重（`tg_cpus()` → `cpuset_num_cpus()`）；没有这个计数，BPF 调度器只能用全机 CPU 数，可能给被 cpuset 限制到少数核的 group 过高份额。任务的有效亲和性含 per-task 限制、不能可靠代表 group 的 cpuset，而 BPF 直接读 cpuset 需要 CO-RE 访问私有 cgroup/cpuset 结构（含继承解析），跨内核版本脆弱。v1 里为保护 `cpuset_num_cpus()` 的 `is_in_v2_mode()` 调用的 1/3 补丁，在 v2 中因 Waiman Long 独立的 cpuset 修复（覆盖一个 cgroup 文件系统 rebind 竞态的潜在 UAF）而不再需要，被 drop。

## 技术方案

（承接）v2 收为两片：

1. **`sched_ext: Introduce scx_bpf_cgroup_nr_cpus()`**：新增 `__bpf_kfunc u32 scx_bpf_cgroup_nr_cpus(struct cgroup *cgrp)`，返回 `cpuset_num_cpus(cgrp)`。计数与 CPU/CID 编号无关，cpu-form 与 cid-form 调度器在任何上下文都可用；附 `compat.bpf.h` 兼容包装（旧内核回退 `nr_cpu_ids`）。
2. **`selftests/sched_ext: Test scx_bpf_cgroup_nr_cpus()`**：新建 cgroup-v2 子树（子拥有 cpuset、叶继承），用 `BPF_PROG_TYPE_SYSCALL` 程序采样 kfunc 与 `cpuset.cpus.effective` 对比，覆盖有效/继承 cpuset、允许 CPU 变更、有无挂调度器两种调用；最后 disable cpuset 使两级继承父 cpuset。带 `Assisted-by: LLM`。

## 版本演进与当前进展

- v1（09-29，`<20260929084124.626693-1-arighi@nvidia.com>`）：3 补丁，含保护 `is_in_v2_mode()` 的 cpuset 前置补丁。
- v2（09-30，`<20260930090049.1035813-1-arighi@nvidia.com>`）：drop cpuset RCU guard 补丁、改为依赖 Waiman Long 的 cpuset 修复；系列 2 补丁。

## Maintainer 意见与讨论焦点

当日无回帖。作者即 sched_ext 维护者，系列自投 `sched_ext/for-7.4`，待 Tejun Heo 审阅/收取。v2 的关键依赖 Waiman Long 的 cpuset 修复（`20260930031833.660267-1-longman@redhat.com`）尚未见合入。

## 合入评估

*likelihood=high*。作者是 sched_ext 维护者本人、系列自含 kernel 实现 + compat 包装 + selftest、语义复用 fair 的 `cpuset_num_cpus()`（低风险），v2 精简后更聚焦。*blocking_issues*：尚未见 Tejun 审阅/收取；依赖 Waiman Long 的 cpuset 修复先行合入。*next_action*：等 Tejun 审阅、且 Waiman 的 cpuset 修复落地后应用进 sched_ext/for-7.4。

## 效果评估

无性能数据；属调度器编程接口能力补充，效果体现在让层级式 BPF 调度器（如 scx_eevdf）能按 cgroup 真实 CPU 数约束权重，邮件未附量化对比。

## 我可以参与的点

- `review`：核对 `scx_bpf_cgroup_nr_cpus()` 的 `KF_RCU` 与 `cpuset_num_cpus()` 调用是否满足 kfunc 上下文/生命周期约束，以及 cgroup v1 无 v2_mode 时的回退语义。
- `testing`：在 cgroup v1/v2 两种模式下用 scx 示例调度器验证返回的 CPU 数与 `cpuset.cpus.effective` 一致（含 partition root、热插拔场景）。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20260930090049.1035813-1-arighi@nvidia.com/
- lore（v1 cover）: https://lore.kernel.org/all/20260929084124.626693-1-arighi@nvidia.com/
- Waiman 的 cpuset 修复: https://lore.kernel.org/r/20260930031833.660267-1-longman@redhat.com/
