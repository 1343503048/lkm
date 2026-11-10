---
id: sched-20261110-007
date: '2026-11-10'
subject: Hierarchical Constant Bandwidth Server
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261109163616.195264-1-yurand2000@gmail.com>
lore_url: https://lore.kernel.org/all/20261109163616.195264-1-yurand2000@gmail.com/
authors:
- Yuri Andriaccio
- Luca Abeni
maintainers_involved: []
current_version: v7
patch_series:
- version: v7
  msgid: <20261109163616.195264-1-yurand2000@gmail.com>
  date: '2026-11-10'
  summary: 29 补丁：dl-server 化 rt-cgroup 带宽，集成 cpuset/hotplug/multi-cpu，非特权 FIFO/RR
  review_outcome: 当日无评审回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 仍处 RFC，需 sched/rt + deadline 维护者逐条评审
  - 删除 cgroups-v1 与 RT_GROUP_SCHED 需与既有删除讨论闭环
  next_action: 向维护者请求 v7 评审，确认 deadline server 复用与 hotplug/cpuset 集成
contribution_opportunities:
- kind: review
  description: 就 deadline server 复用与 cpuset/hotplug 集成补丁给评审意见
- kind: testing
  description: 验证 cpu.rt.max per-cpu override、hotplug 带宽保持与非特权 FIFO/RR 隔离
- kind: discussion
  description: 若团队依赖 RT_GROUP_SCHED，提供真实用例反馈助力 HCBS 设计收敛
generated_at: '2026-11-11T09:00:00+08:00'
source_email_count: 28
related_articles: []
tags:
- rt
- deadline
- dl_server
- cgroup
- rt_bandwidth
title: Hierarchical Constant Bandwidth Server
layout: article
---

## TL;DR

Yuri Andriaccio 发第 7 版 RFC（29 补丁），用层次化 Constant Bandwidth Server（HCBS）替换现有 `RT_GROUP_SCHED` 机制，为 rt-cgroup 提供理论上更稳健、且与 SCHED_DEADLINE/SCHED_EXT 一致的带宽隔离。v7 相对 v6 变化巨大：rebase 到 7.4-rc1、修掉 v6 评审与 sashiko 指出的大量 bug，并新增 dl_freq_invariant 标志、cgroup-v2 接口重构、cpuset/cpu 控制器集成、hotplug 集成、非特权 FIFO/RR 任务支持、HRTICK_DL、dl_server per-cpu override（multi-cpu）等。已在 OSPM25/26 报告。当日无评审回复，仍为 RFC。

## 背景与问题

现有 `RT_GROUP_SCHED` 实现早已腐坏（启用后 SCHED_FIFO/RR 因 cgroup 无 runtime 失败、cgroup v2 无法分配 runtime、SCHED_DEADLINE 准入卡死），社区此前已讨论到「删除它需要 HCBS 替代」（见 `sched: Remove CONFIG_RT_GROUP_SCHED` 线）。HCBS 用 deadline server 机制为 rt-cgroup 提供带宽隔离：管理员创建并管理 RT 带宽，给定 SCHED_DEADLINE 的隔离属性，普通用户在该带宽内执行 FIFO/RR 任务不会导致饥饿或偷时间。系列曾在 OSPM25/26 报告，LWN 有机制摘要 [1] 与最新进展 [2]。

## 技术方案

v7 的核心理念：把 RT_GROUP_SCHED 的记账替换为逐 cgroup 的 deadline server（dl_server），并做大量机制性铺陈。cover 列出的 v7 主要更新：rebase 到 7.4-rc1；修 v6 评审 + sashiko 发现的多数 bug；引入 `dl_freq_invariant` 标志（强制 fair/ext server 频率/容量不变、而 HCBS server 允许随执行时间伸缩，实现容量感知的带宽预留）；重构 cgroup-v2 接口（`cpu.rt.internal` 改名 `cpu.rt.effective.local`、修 internal runtime 舍入误差）；更新 balance callbacks 支持同时平衡多个 cgroup；允许 cgroup 内非特权 FIFO/RR 任务；允许 HRTICK_DL；集成 `cpu` 与 `cpuset` 控制器；集成 hotplug；引入 dl_server override（旧称 multi-runtime/multi-CPU，通过写 `cpu.rt.max` 对 CPU 子集设置 per-cpu runtime/period override）。

29 补丁从底层重构到特性：01-10 是 deadline/rt 内部结构改造（区分 dl_rq/my_q、hcbs 结构体、禁用 RT_GROUP_SCHED、移除旧结构、dl-server ops、cgroup 接口）；12-21 是记账/迁移/回调（把 rt-cgroup 带宽纳入 deadline 准入、HCBS 迁移、平衡回调）；23-25 是准入与 HRTICK；26 是文档；27-29 是 cpuset 集成与多 CPU 支持。补丁 21 出自 Luca Abeni。

## 版本演进与当前进展

*current_version: v7（2026-11-10 收到，`<20261109163616.195264-1-yurand2000@gmail.com>`）*。v1-v6 未在本 digest 缓存中出现，本文据 v7 cover 与 28 封补丁正文撰写（缺 26/29 文档补丁，其 subject 从全量清单取得）。当日无评审回复。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。系列仍为 RFC，历史上维护者（含 Peter/Tejun）在 RT_GROUP_SCHED 讨论中已把 HCBS 定为替代前提（见 related <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-009-sched-remove-config-rt-group-sched.html">sched-20261106-009</a>），但 v7 本身的逐条评审尚未在当日窗口出现。无 NAK。

## 合入评估

*likelihood=unknown*。RFC v7、29 补丁、且涉及移除 cgroups-v1 与 RT_GROUP_SCHED 这类需社区共识的改动，当日无人表态，不宜预判。*blocking_issues*：① 仍处 RFC、需 sched/rt + deadline 维护者逐条评审；② 删除 cgroups-v1 与 RT_GROUP_SCHED 需与既有「Remove CONFIG_RT_GROUP_SCHED」讨论闭环（该删除方向明确 blocked on HCBS）。*next_action*：向维护者请求 v7 评审，重点确认 deadline server 复用与 hotplug/cpuset 集成的正确性。

## 效果评估

无性能数据。cover 以理论稳健性与隔离正确性立论，未给 benchmark；非特权 FIFO/RR 的论证是安全论证（管理员控带宽 + SCHED_DEADLINE 隔离 ⇒ 用户无法饥饿他人），非量化效果。

## 我可以参与的点

- **review**：v7 大量补丁尚无人类维护者评审，可就 deadline server 复用（patch 05-13）与 cpuset/hotplug 集成（patch 27-29）给评审意见。
- **testing**：在真实 rt-cgroup 场景验证 `cpu.rt.max` per-cpu override、hotplug 下带宽保持与非特权 FIFO/RR 的隔离。
- **discussion**：若团队依赖 `RT_GROUP_SCHED`，这是 HCBS 替代方案的落地窗口，提供真实用例反馈有助于设计收敛。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109163616.195264-1-yurand2000@gmail.com/
- [1] 机制摘要: https://lwn.net/Articles/1021332/
- [2] 最新进展: https://lwn.net/Articles/1078696/
