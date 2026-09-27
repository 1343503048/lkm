# sched_ext: Add a CID NUMA node lookup kfunc

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260925-018：Andrea Righi 为 sched_ext/for-7.4 新增 `scx_bpf_cid_node()` kfunc，让 CID-form 调度器拿到某 CID 所属的物理 NUMA 节点（例如在该节点分配 arena 内存）。当日刚发、无回帖。
- sched-20260927-003（今天）：Tejun Heo 回复「Applied to sched_ext/for-7.4」，本补丁正式收入 sched_ext 维护树、随 for-7.4 提交队列面向下一个合并窗口。

## 背景与问题

（承接 sched-20260925-018）CID-form 的 sched_ext 调度器（以紧凑 ID 而非 CPU 号组织任务）有时需要知道某 CID 落在哪个**物理 NUMA 节点**上——典型用途是把 arena 内存分配在该节点、保持本地化。现有 `scx_bpf_cpu_node()` 只对 CPU-form 调度器开放，CID 拓扑里的 node index 也不是物理 NUMA node ID，缺一个 CID → 物理 NUMA node 的查询口。

## 技术方案

（承接 sched-20260925-018）新增 kfunc `scx_bpf_cid_node(s32 cid, const struct bpf_prog_aux *aux)`：RCU 保护下取 scheduler，`scx_cid_to_cpu()` 得到代表 CPU，再 `cpu_to_node()` 返回物理 NUMA node；cid 无效或无 scheduler 时返回 `NUMA_NO_NODE`。该 kfunc 只在 CID 支持开启时存在，BPF 调度器可用其存在性探测「NUMA-aware CID lookup」是否可用；`tools/sched_ext/include/scx/compat.bpf.h` 提供返回 `NUMA_NO_NODE` 的兼容桩。规模 30 insertions。

## 版本演进与当前进展

- v1（2026-09-25，`<20260925144604.2451177-1-arighi@nvidia.com>`）：首发（对应 sched-20260925-018）。
- 09-27 03:52：Tejun 回复「Applied to sched_ext/for-7.4」，无附言、无修改要求，直接合入。

## Maintainer 意见与讨论焦点

Tejun Heo 今日表态即合入（仅「Applied to sched_ext/for-7.4」一句），此前 sched-20260925-018 标注的待讨论点（kfunc 的「存在性即可用性探测」惯例是否契合稳定约定）未见 Tejun 提出异议。无分歧记录。

## 合入评估

*likelihood=merged*：`status=merged_tip`，已收入 sched_ext/for-7.4 提交队列。需注意 for-7.4 是面向下一个合并窗口（v7.4）的维护分支，尚非 tip/sched。*blocking_issues*：无；是否最终随 7.4 合并窗口进主线由后续 GIT PULL 决定。*next_action*：跟踪 Tejun 对 for-7.4 的整体 GIT PULL。

## 效果评估

无运行时数据；API 补全类 feature，收益是 NUMA-aware arena 分配成为可能。

## 我可以参与的点

- `extend`：基于 `scx_bpf_cid_node()` 写一个 NUMA-aware arena 分配的示例 CID 调度器，验证 CID → NUMA node 映射与跨节点内存本地化效果，回帖补充实测。

## 参考链接

- 补丁（线程根）: https://lore.kernel.org/all/20260925144604.2451177-1-arighi@nvidia.com/
- Tejun applied 回执: https://lore.kernel.org/all/936f4e6383cdfed5198ac3edba80ae13@kernel.org/

---
id: sched-20260927-003
date: 2026-09-27
subject: "sched_ext: Add a CID NUMA node lookup kfunc"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<20260925144604.2451177-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260925144604.2451177-1-arighi@nvidia.com/"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Tejun Heo"
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260925144604.2451177-1-arighi@nvidia.com>"
    date: 2026-09-25
    summary: "新增 scx_bpf_cid_node() kfunc：CID → 物理 NUMA node，无 scheduler/cid 无效时返回 NUMA_NO_NODE，附 compat 兼容桩。"
    review_outcome: "Tejun Heo 2026-09-27 回复 Applied to sched_ext/for-7.4。"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
merge_assessment:
  likelihood: merged
  blocking_issues:
    - "无：已收入 sched_ext/for-7.4（面向 v7.4 合并窗口，非 tip/sched）"
  next_action: "跟踪 Tejun 对 for-7.4 的整体 GIT PULL 确认进主线"
contribution_opportunities:
  - kind: extend
    description: "基于 scx_bpf_cid_node() 写 NUMA-aware arena 分配的示例 CID 调度器，验证映射与内存本地化效果"
generated_at: "2026-09-28T09:00:00"
source_email_count: 1
related_articles:
  - sched-20260925-018
tags:
  - sched_ext
  - topology
---