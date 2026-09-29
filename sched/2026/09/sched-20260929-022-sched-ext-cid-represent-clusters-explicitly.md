# sched_ext: cid: Represent clusters explicitly

> **subject**：`sched_ext: cid: Represent clusters explicitly`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20260926-005：Andrea Righi（sched_ext 维护者）新发单枚补丁，让 sched_ext 的 CID 拓扑把「cluster」（同一 LLC 内共享 L2 等更紧资源的核组）显式表示为一段连续 CID 区间。
- sched-20260927-001：Tejun Heo 密集 review（v2 review 标注 Claude 生成），核心诉求是让 cluster 层级「inclusive」；Righi 依次回 v2（core 自为 cluster）、v3（改用 inclusive mask）。方向收敛，待 v3 审阅。
- sched-20260929-022（今天）：Tejun Heo 回复「Applied to sched_ext/for-7.4」，v3（inclusive mask 版本）正式合入。

## 背景与问题

（承接 sched-20260926-005）sched_ext 的 CID 拓扑把每个层级（core/LLC/NUMA node）表示成一段连续 CID 区间，唯独 cluster 层级（对应 `SD_CLUSTER` 调度域）不成立，`struct scx_cid_topo` 也没有字段标识 CPU 属于哪个 cluster，CID-form 调度器无法表达 cluster 级拓扑。今天无新背景，进展是 v3 合入。

## 技术方案

（承接）在 `kernel/sched/ext/cid.c` 按 cluster 枚举核并新增 `cluster_cid`/`cluster_idx` 字段；v3 采用 Tejun 建议的「inclusive mask」语义：`cpumask_or(cluster_scratch, topology_cluster_cpumask(xcpu), topology_sibling_cpumask(xcpu))` 再 `cpumask_and(..., llc_scratch)`——无独立 cluster 层级的 core 自成一个 cluster（cluster_cid = core_cid、cluster_idx 稠密），与 LLC 同宽的 L2 每 LLC 一个 cluster；并更新 kerneldoc、说明 shard 可能切分 cluster、遍历改 cluster 顺序。该 v3 已叠在 `scx_bpf_cid_topo()` 的 size 参数修复（for-7.3-fixes）之上。

## 版本演进与当前进展

*current_version: v3*（`<20260927133719.3458770-1-arighi@nvidia.com>`）。v1（09-26）→ v2（09-27 fallback 改 core 自为 cluster）→ v3（09-27 inclusive mask）→ 09-29 Tejun 收「Applied to sched_ext/for-7.4」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（sched_ext 维护者）：v1/v2 两轮 review 敲定 inclusive 语义与 ABI 前向兼容（size 参数），09-29 确认「Applied to sched_ext/for-7.4.」。
- **Andrea Righi**（作者/维护者）：逐条采纳 Tejun 意见落地 v3，唯一保留 subject 的 `cid:` 前缀（未按 Tejun 建议改）。
- 无 NAK；v3 已获 Tejun 收取，subject 命名的保留未构成障碍。

## 合入评估

*likelihood=merged*。v3 已合入 sched_ext/for-7.4（inclusive cluster 表示，ABI 隐患已由 size 参数修复打底）。*blocking_issues*：无（等待随 7.4 合并窗口进 mainline）。*next_action*：跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR。

## 效果评估

无性能数据（拓扑描述类 feature）；此前作者给出 Intel Core i7-13800H 的结构验证（P-core 对形成 two-CID cluster、E-core 模块 four-CID cluster、cluster_idx 全 8 cluster 稠密）。

## 我可以参与的点

- `testing`：在 AMD 混合（Zen4/Zen4c）或非 x86 平台验证 `scx_bpf_cid_topo()` 的 cluster_cid/cluster_idx 输出与 fallback/稠密索引行为（尤其 `CONFIG_SCHED_CLUSTER=n`）。

## 参考链接

- lore（v3 补丁）: https://lore.kernel.org/all/20260927133719.3458770-1-arighi@nvidia.com/
- lore（Tejun 收取）: https://lore.kernel.org/all/55340bef0e2f44cde6bd5f0616b68da0@kernel.org/

---
id: sched-20260929-022
date: 2026-09-29
subject: "sched_ext: cid: Represent clusters explicitly"
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: "<20260927133719.3458770-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20260927133719.3458770-1-arighi@nvidia.com/"
authors:
  - "Andrea Righi"
maintainers_involved:
  - "Tejun Heo"
current_version: v3
patch_series:
  - version: v1
    msgid: "<20260926152306.3190774-1-arighi@nvidia.com>"
    date: 2026-09-26
    summary: "按 cluster 枚举核新增 cluster_cid/cluster_idx；无 cluster 时 cluster_cid 取 LLC 自身、cluster_idx 置 -1"
    review_outcome: "Tejun 提出 inclusive 语义 + size 参数"
  - version: v2
    msgid: "<20260926212017.3351797-1-arighi@nvidia.com>"
    date: 2026-09-27
    summary: "fallback 改为 core 自为 cluster、cluster_cid=core_cid、cluster_idx 稠密"
    review_outcome: "Tejun（Claude review）建议改 inclusive mask"
  - version: v3
    msgid: "<20260927133719.3458770-1-arighi@nvidia.com>"
    date: 2026-09-27
    summary: "改用 inclusive mask；更新 kerneldoc；说明 shard 切分；遍历改 cluster 顺序"
    review_outcome: "09-29 Tejun Applied to sched_ext/for-7.4"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.4"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "跟踪 sched_ext/for-7.4 随 7.4 合并窗口的 PR"
contribution_opportunities:
  - kind: testing
    description: "在 AMD 混合或非 x86 平台验证 scx_bpf_cid_topo 的 cluster 输出与 fallback 行为（含 CONFIG_SCHED_CLUSTER=n）"
generated_at: "2026-09-30T01:15:00"
source_email_count: 1
related_articles:
  - sched-20260927-001
tags:
  - sched_ext
  - topology
---