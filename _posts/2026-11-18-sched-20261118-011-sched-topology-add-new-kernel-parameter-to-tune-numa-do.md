---
id: sched-20261118-011
date: '2026-11-18'
subject: 'sched/topology: Add new kernel parameter to tune NUMA domain flags'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261117131854.924760-1-wujianyong@hygon.cn>
lore_url: https://lore.kernel.org/all/20261117131854.924760-1-wujianyong@hygon.cn/
authors:
- Jianyong Wu
maintainers_involved:
- Tim Chen
current_version: v1
patch_series:
- version: v1
  msgid: <20261117131854.924760-1-wujianyong@hygon.cn>
  date: '2026-11-17'
  summary: 新增启动参数按 NUMA 距离独立调 FORK/EXEC/WAKE_AFFINE 标志
  review_outcome: Tim 建议复用 node_reclaim_distance + relax_domain_level
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 维护者倾向复用既有机制，作者坚持独立参数
  next_action: 作者回应 Tim 的复用建议，评估新参数通用性
contribution_opportunities:
- kind: testing
  description: 跨平台对比 relax_domain_level 与新参数的调度标志控制效果
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- topology
- numa_balancing
- load_balance
title: 'sched/topology: Add new kernel parameter to tune NUMA domain flags'
layout: article
---

## TL;DR

Jianyong Wu（Hygon）发补丁新增内核启动参数，用于按 NUMA 距离阈值独立微调 `SD_BALANCE_FORK`/`SD_BALANCE_EXEC`/`SD_WAKE_AFFINE` 三个调度域标志。Tim Chen（sched/cache 维护者）评审时建议改用现成的 `node_reclaim_distance`（arch 侧可设 32）与 `relax_domain_level`（可清 `SD_BALANCE_NEWIDLE`）而非引入新参数；Jianyong 回应三点理由（工作负载相关、机器拓扑相关、FORK/EXEC 与 WAKE_AFFINE 需独立阈值），并承认忘了 `relax_domain_level` 存在、将移除 NEWIDLE 部分。刚进入 review，方向仍在博弈。

## 背景与问题

NUMA 调度域上 `SD_BALANCE_FORK`/`SD_BALANCE_EXEC`/`SD_WAKE_AFFINE` 三个标志决定了「fork/exec 的新任务放多远」「wakee 能被拉到离 waker 多远」。作者在 Hygon 平台上发现：把这些标志从跨 NUMA 层级上剥离，能改善 fork/exec 密集 benchmark（避免子进程先堆在本地节点），但代价是长运行子进程聚集、pipe 通信等场景受益/受损依赖拓扑。现状只有 `node_reclaim_distance` 一个全局阈值同时牵制三个标志，且它还兼做 mm reclaim 的 cutoff，无法按需独立调节。

## 技术方案

作者方案：新增启动参数，按 NUMA 距离阈值独立控制上述三个标志（`fork`/`exec`/`wake_affine`/`newidle` 等子项）。Tim Chen 的替代建议：

- Hygon 可像 AMD（`init_amd_zen_common()` 设 `node_reclaim_distance=32`）一样在 arch 侧设 `node_reclaim_distance`，保留 FORK/EXEC 在正确层级；
- 用现有启动参数 `relax_domain_level=<level>`（`set_domain_attribute()` 里清 `SD_BALANCE_NEWIDLE`）即可清 NEWIDLE 标志，不必新增参数。

Jianyong 回应三点坚持新参数的理由：① 最佳设置依赖工作负载（fork/exec 密集 vs 长运行子进程、pipe 通信 vs wakeup 延迟），同一机器无单一最优值；② 最佳阈值依赖机器拓扑（机器 A 所有节点距离 ≤27，机器 B 跨 socket 29-38，arch 侧一个数无法同时适配）；③ FORK/EXEC 与 WAKE_AFFINE 语义不同、需要独立阈值，而 `node_reclaim_distance` 把它们绑在一起，且改动它还会牵连 mm reclaim（`zone_allows_reclaim()`、khugepaged）。同时承认忘了 `relax_domain_level` 存在，将移除 NEWIDLE 部分。

## 版本演进与当前进展

*current_version: v1（2026-11-17 发出，`<20261117131854.924760-1-wujianyong@hygon.cn>`）*。今日为评审日：Tim 建议复用现成旋钮，作者逐条回应并承诺移除 NEWIDLE 部分。

## Maintainer 意见与讨论焦点

- **Tim Chen（sched/cache 维护者）**：主张复用 `node_reclaim_distance` + `relax_domain_level`，避免为同一标志引入第二个启动参数；并引用其此前对 Hygon 上 Kunyu 的同类建议。
- **Jianyong Wu（作者）**：坚持需要独立、按工作负载/拓扑可调的参数，给出三点理由；部分让步（移除 NEWIDLE 部分）。
- 分歧核心：新增用户可调 knob vs 复用既有 arch 阈值/启动参数，尚未收敛。

## 合入评估

*likelihood=unknown*。单一平台（Hygon）motivated 的新启动参数，维护者倾向复用既有机制，方向尚在博弈。*blocking_issues*：① 维护者建议复用 node_reclaim_distance/relax_domain_level，作者坚持独立参数；② 尚未评估新参数是否值得进主线的通用性。*next_action*：作者回应 Tim 的复用建议（是否接受 relax_domain_level 替代 NEWIDLE、其余两个标志是否仍坚持独立）。

## 效果评估

作者在 Hygon 机器上以 schbench（`NI_RANDOM`）等 benchmark 论证不同设置的影响，但当日缓存未给具体数字（Tim 邮件中请作者用 relax_domain_level 重跑 schbench 验证）。效果数据未获取到。

## 我可以参与的点

- **testing**：在 Hygon/AMD/Intel 多 NUMA 平台上用 `relax_domain_level` 与作者的新参数分别跑 schbench/fork 密集 benchmark，对比两者对 FORK/EXEC/WAKE_AFFINE 标志的控制差异，为「是否值得新参数」提供跨平台数据。

## 参考链接

- lore thread（v1）: https://lore.kernel.org/all/20261117131854.924760-1-wujianyong@hygon.cn/
- Tim Chen 的评审: https://lore.kernel.org/all/0f6295ad41cce262149b939c8a245df76bfe5719.camel@linux.intel.com/
- Jianyong 的回应: https://lore.kernel.org/all/29b6fa8e9bd64e61b3f20516756c3c06@hygon.cn/
