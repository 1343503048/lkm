---
id: sched-20260926-005
date: 2026-09-26
subject: 'sched_ext: cid: Represent clusters explicitly'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260926152306.3190774-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260926152306.3190774-1-arighi@nvidia.com/
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: v1
generated_at: '2026-09-27T01:20:00'
authors:
- Andrea Righi
maintainers_involved: []
patch_series:
- version: v1
  msgid: <20260926152306.3190774-1-arighi@nvidia.com>
  date: 2026-09-26
  summary: CID 拓扑显式表示 cluster：连续 CID 区间 + scx_cid_topo 新增 cluster_cid/cluster_idx
  review_outcome: 暂无回帖
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 暂无回帖，需 Tejun Heo 或其他 reviewer 审阅
  - 无 cluster 层级 / cluster 与 LLC 同宽等边界需覆盖验证
  next_action: 等待 review；可补非 x86 或无 cluster 平台的行为验证
contribution_opportunities:
- kind: review
  description: 核查 cluster_cid 在 cluster 层级不存在/与 LLC 同宽时的取值是否与 SD_CLUSTER 丢弃规则一致
- kind: testing
  description: 在无 cluster 或非 x86 平台验证 cluster_idx=-1 / cluster_cid=llc_cid 回落行为与 scx_bpf_cid_topo
    输出
source_email_count: 1
related_articles: []
tags:
- sched_ext
- topology
- x86
title: 'sched_ext: cid: Represent clusters explicitly'
layout: article
---

## TL;DR

Andrea Righi（sched_ext 维护者）为 sched_ext/for-7.4 新发的单枚补丁：让 sched_ext 的 CID 拓扑把「cluster」（同一 LLC 内共享 L2 等更紧资源的核组）显式表示为一段连续 CID 区间，并在 `struct scx_cid_topo` 里给出 cluster 归属。目前刚发出、尚无回帖。

## 背景与问题

sched_ext 的 CID 拓扑把每个拓扑层级（core / LLC / NUMA node）表示成一段**连续**的 CID 区间，这在 core、LLC、NUMA node 上都成立，但唯独对 **cluster** 不成立——cluster 是「同一 LLC 内共享 cache 或其他 CPU 局部资源、比 LLC 其余 CPU 更紧密的核组」（对应 `SD_CLUSTER` 调度域）。此外 `struct scx_cid_topo` 目前根本没有字段标识某个 CPU 属于哪个 cluster。CID-form 调度器（用紧凑 ID 而非 CPU 号组织任务）因此无法表达 cluster 级拓扑。

## 技术方案

在 `kernel/sched/ext/cid.c` 的 CID 拓扑构建里显式表示 cluster，五处改动：

- 逐个 cluster 枚举其核，再移动到下一个 cluster（保证 cluster 内 CID 连续）；
- 在 `struct scx_cid_topo` 新增 `cluster_cid` / `cluster_idx` 字段报告 cluster 归属；
- 无 cluster 层级时把 `cluster_cid` 设为 LLC 自身的 CID；
- 无 cluster 层级时 `cluster_idx` 置 -1；
- 没有 cluster 层级的 CPU 视作「只含自己那个 core」的单核 cluster，保持既有遍历顺序不变。

涉及的读取 API（`scx_bpf_cid_topo()`）返回的 cluster 信息随之上线。

## 版本演进与当前进展

v1 刚发出（`<20260926152306.3190774-1-arighi@nvidia.com>`），暂无 review 意见。diffstat：`kernel/sched/ext/cid.c` +71/-…、`cid.h` +12/-…、`types.h` +22/-…，共 88 insertions(+), 17 deletions(-)。

## Maintainer 意见与讨论焦点

本补丁作者即 sched_ext 维护者 Andrea Righi 本人，针对自有 `sched_ext/for-7.4` 树提交；暂无其他维护者（Tejun Heo）或 review 意见，无分歧记录。

## 合入评估

*likelihood=unknown*。刚发出半天，唯一可参考信号是作者自测细节较全（见下）且目标是自有树的 7.4 窗口。*blocking_issues*：暂无回帖，需 Tejun Heo 或其他 reviewer 审阅后确认；cluster 拓扑在 `CONFIG_SCHED_CLUSTER=n` 与畸形拓扑下的边界行为需覆盖。*next_action*：等待 review；作者可补非 x86 或无 cluster 平台的行为验证。

## 效果评估

作者给出一组 Intel i7-13800H（`CONFIG_SCHED_CLUSTER=y`）实测描述：6 个 P-core 开 SMT 占 CPU 0-11、8 个 E-core 分两个 L2 模块占 CPU 12-15 与 16-19、一个 LLC 覆盖全部 20 核。结果：P-core 的 cluster 域退化为其 SMT 对，每个 E-core 模块各自一个 cluster 域；`scx_bpf_cid_topo()` 对 P-core 报告 LLC 的 CID，对两个 E-core cluster 报告各一段连续的 4-CID 区间。属于正确性/拓扑描述验证，无性能数据。

## 我可以参与的点

- `review`：核查 `cluster_cid` 在「cluster 层级不存在」与「cluster 与 LLC 同宽」两类被丢弃的场景下的取值是否与 `sched_domain` 的 SD_CLUSTER 丢弃规则一致。
- `testing`：在无 cluster 层级（或非 x86）平台上验证 `cluster_idx == -1` / `cluster_cid == llc_cid` 的回落行为与 `scx_bpf_cid_topo()` 输出。

## 参考链接

- lore 补丁: https://lore.kernel.org/all/20260926152306.3190774-1-arighi@nvidia.com/
