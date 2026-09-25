---
id: sched-20260925-018
date: 2026-09-25
subject: 'sched_ext: Add a CID NUMA node lookup kfunc'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260925144604.2451177-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260925144604.2451177-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-26T01:15:00'
authors:
- Andrea Righi
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260925144604.2451177-1-arighi@nvidia.com>
  date: 2026-09-25
  summary: 新增 scx_bpf_cid_node() kfunc，CID → 物理 NUMA node，附兼容桩
  review_outcome: 无回帖
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  next_action: 等 Tejun 对 CID kfunc 命名与兼容桩的 review
contribution_opportunities:
- kind: review
  description: 审读 scx_bpf_cid_node 在 cid 无效/无 scheduler 时返回 NUMA_NO_NODE 的语义与 RCU
    保护边界
- kind: extend
  description: 基于该 kfunc 写一个 NUMA-aware arena 分配的示例 CID 调度器
source_email_count: 1
related_articles: []
tags:
- sched_ext
title: 'sched_ext: Add a CID NUMA node lookup kfunc'
layout: article
---

## TL;DR

Andrea Righi 为 sched_ext/for-7.4 新发的单枚补丁：新增 `scx_bpf_cid_node()` kfunc，让 CID-form 调度器拿到某 CID 所属的物理 NUMA 节点（例如用于在该节点上分配 arena 内存）。今日刚发、无回帖。

## 背景与问题

CID-form 的 sched_ext 调度器（以紧凑 ID 而非 CPU 号组织任务）有时需要知道某个 CID 落在哪个**物理 NUMA 节点**上——典型用途是把 arena 内存分配在该节点、保持本地化。但现有的 `scx_bpf_cpu_node()` 只对 CPU-form 调度器开放；CID 拓扑里的 node index 也不是物理 NUMA node ID，不能直接映射。缺一个 CID → 物理 NUMA node 的查询口。

## 技术方案

新增 kfunc `scx_bpf_cid_node(s32 cid, const struct bpf_prog_aux *aux)`：在 RCU 保护下取 scheduler，`scx_cid_to_cpu()` 得到代表 CPU，再 `cpu_to_node()` 返回物理 NUMA node；cid 无效或无 scheduler 时返回 `NUMA_NO_NODE`。与 `scx_bpf_cpu_node()` 不同，该 kfunc 只在 CID 支持开启时存在，BPF 调度器可用它的存在性来探测「NUMA-aware CID lookup」是否可用。同时在 `tools/sched_ext/include/scx/compat.bpf.h` 提供返回 `NUMA_NO_NODE` 的兼容桩。规模：kernel/sched/ext/cid.c +24、tools 两处 +1/+5，共 30 insertions。

## 版本演进与当前进展

- v1（2026-09-25，`<20260925144604.2451177-1-arighi@nvidia.com>`）：首发，带 `PATCH sched_ext/for-7.4` 标记，今日无回帖。

## Maintainer 意见与讨论焦点

今日无人回帖；Tejun Heo（sched_ext 维护者）尚未表态。设计上有一个可讨论点：kfunc 的「存在性即可用性探测」惯例（与 `scx_bpf_cpu_node` 的 CPU-form 限定相对照）是否符合 sched_ext kfunc 稳定约定。

## 合入评估

*likelihood=unknown*。单枚、面向 for-7.4，无回帖。*blocking_issues*：无 review。*next_action*：等 Tejun 对 CID kfunc 命名与兼容桩的 review。

## 效果评估

无运行时数据；属 API 补全类 feature。

## 我可以参与的点

- `review`：`scx_bpf_cid_node` 在 cid 无效/无 scheduler 时返回 NUMA_NO_NODE 的语义，与 `scx_bpf_cid_to_cpu` 的一致性和 RCU 保护边界值得审读。
- `extend`：基于该 kfunc 写一个 NUMA-aware arena 分配的示例 CID 调度器。

## 参考链接

- 补丁: https://lore.kernel.org/all/20260925144604.2451177-1-arighi@nvidia.com/
