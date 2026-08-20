---
subject: 'sched/numa: Apply remote socket distance averaging for Hygon 7447V'
id: sched-20260803-009
date: 2026-08-03
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Rong Tao
maintainers_involved:
- Peter Zijlstra
- Mel Gorman
- Ingo Molnar
current_version: v3
patch_series:
- version: v3
  msgid: <unknown>
  date: 2026-08-03
  summary: Hygon 7447V（8 节点 Rome 级）采用模组化布局：NUMA 节点 0-3 在 socket0、4-7 在 socket1。远程
    socket 距离统一为 32，丢失『本地节点 vs 远端 socket 的不同寻址成本』信息。改为对远程 socket 节点距离取平均，区分 intra-socket
    与 inter-socket 远程。
  review_outcome: Ingo Molnar 给出 Acked-by，认可把性能反馈纳入标准 review 流程；此前 Dave Hansen 询问
    AMD 是否应同样的改动。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 已获 Ingo Acked-by，等待 PeterZ/Mel 最终接收；AMD 同款场景的对称性可顺带确认。
contribution_opportunities:
- kind: testing
  description: 可在 Hygon 7447V / AMD Rome 上以 numa 基准（如 stream/numactl 跨节点带宽）验证距离平均后任务放置是否更优，回帖对比数据补强作者提供的效果证据。
generated_at: '2026-08-04T00:20:00'
source_email_count: 2
related_articles: []
tags:
- numa
- topology
- x86
- hygon
title: 'sched/numa: Apply remote socket distance averaging for Hygon 7447V'
layout: article
---

# sched/numa: Hygon 7447V 远程 socket 距离平均


## TL;DR
`sched/numa` 针对 Hygon 7447V 的模块化布局，把远程 socket 节点距离取平均以区分 intra/inter-socket 远程代价。已获 Ingo Acked-by，合入可能性高。

## 背景与问题
Hygon 7447V 是 Rome 代际的 8 节点处理器：节点 0-3 在一个 socket、4-7 在另一 socket，每个 socket 内有 4 个 CCD。SRAT/SLIT 表把所有「跨 socket」节点的距离统一标为 32，但本地节点到同 socket 其他节点的成本（intra-socket 远程）明显低于到另一 socket 的节点（inter-socket 远程）。统一距离让 NUMA 平衡器无法区分这两种远程，导致任务放置偏离最优。

## 技术方案
对「远程 socket」节点的距离做平均：保留 intra-socket 远程节点的原始较小距离，把 inter-socket 远程节点的距离用平均值表达，从而在 SLIT 表缺失细分信息的情况下，让 sched/numa 的 locality 计算能区分两种远程层级。邮件附性能提升数据作为依据。

## 版本演进与当前进展
当前 v3（2026-08-03），作者 Rong Tao。Ingo Molnar 在 review 中明确给出 `Acked-by`，并强调「性能反馈的邮件应纳入标准 review 流程」。此前 Dave Hansen 曾提问 AMD 是否应做同样的改动（对称性议题）。

## Maintainer 意见与讨论焦点
- Ingo Molnar：Acked-by，认可以性能数据驱动 review。
- Dave Hansen：提出 AMD Rome 是否也应同样处理（架构对称性）。

无方向性反对，焦点在「是否扩展到 AMD 同款」。

## 合入评估
合入可能性 high。已获关键 maintainer Acked-by，纯属拓扑描述修正，无功能风险。

## 效果评估
邮件附性能提升数据（作者提供的 numa 工作负载对比）作为效果证据，属「有实证」的优化。可进一步在 Hygon/AMD 上复测确认。

## 我可以参与的点
- 在 Hygon 7447V 或 AMD Rome 上用 numa 基准复测，回帖对比数据，补强作者效果证据；并可跟进 Dave Hansen 的对称性问题，确认 AMD 是否需同样的改动。

## 参考链接
- lore thread: 未获取到
