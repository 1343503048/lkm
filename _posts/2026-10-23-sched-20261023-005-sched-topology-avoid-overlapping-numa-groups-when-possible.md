---
id: sched-20261023-005
date: 2026-10-23
subject: 'sched/topology: Avoid overlapping NUMA groups when possible'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <tencent_3A95EEAE75A6E08A5DB20A9A6610AA4B0B09@qq.com>
lore_url: https://lore.kernel.org/all/tencent_3A95EEAE75A6E08A5DB20A9A6610AA4B0B09@qq.com/
authors:
- Fengyu Wang
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <tencent_3A95EEAE75A6E08A5DB20A9A6610AA4B0B09@qq.com>
  date: 2026-10-23
  summary: build_overlap_sched_groups 收缩重叠 remote 候选到更小 NUMA 子域
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无 review
  - 未测工作负载性能/放置影响
  - 触及历史敏感的拓扑构建代码
  next_action: 需 reviewer 确认收缩策略无漏覆盖，并补性能数据
contribution_opportunities:
- kind: review
  description: 核对只下沉 NUMA 子域的边界，确认非对称拓扑下不丢覆盖
- kind: testing
  description: 在真实 NUMA 硬件上量化偏差修正对利用率分布/fork 放置的收益
generated_at: '2026-10-24T09:04:00'
source_email_count: 1
related_articles: []
tags:
- topology
- numa
title: 'sched/topology: Avoid overlapping NUMA groups when possible'
layout: article
---

## TL;DR
Fengyu Wang（海光）发往 sched 的 RFC 单补丁：修正 `build_overlap_sched_groups()` 在部分 NUMA 拓扑（环形四节点即一例）下生成的 sched group 会互相重叠，导致同一 CPU 的负载/容量被重复计入、域平均值产生偏差。方案是「保留本地 child span、把重叠的 remote 候选下沉到更小的 NUMA 子域，直到其 child 与已覆盖 CPU 不相交」。作者用 QEMU/KVM + `-numa dist` 启动验证 350 个域全部通过、EPYC 拓扑 group 不变；**未测工作负载性能/进程放置影响**；邮件标注 `Assisted-by: LLM`。无 review，属 RFC 早期。

## 背景与问题
以四节点环形距离表（节点 0-3，距离 20/30 交错）为例：CPU0 在距离 30 处看到的两个 sched group 为 `local:{0,1,3}`、`remote:{1,2,3}`——节点 1、3 被两侧同时计入、节点 0、2 只计入一次。把 group 负载除以「合计容量」并不能抵消这种不等权，域平均值因此有偏。等容节点下，节点 1、3 的共享负载在 group 负载差中抵消，剩下节点 0 与 2 的差异；但 source-rq 选择可能从节点 1 或 3（而非 2）拉任务，改变 local group 内部放置却并未直接减轻节点 2 的负载。

## 技术方案
单补丁（`kernel/sched/topology.c`，+42/-8），核心改动在 `build_overlap_sched_groups()`：

- 引入 `shrink` 标志：若存在「在本次 level 缺失、需靠分组覆盖」的 CPU（`for_each_cpu_andnot(span, span(child))` 中 sibling 不含该 CPU），则**不收缩**，避免漏覆盖。
- 对 remote 候选（sibling），当其 child 与 `covered` 已覆盖 CPU 相交时，逐层下沉（`for (tmp = sibling; tmp->child; tmp = tmp->child)`）直到 `child` 与 `covered` 不相交即采用该子域；**只下沉 NUMA 子域**（`tmp->child->flags & SD_NUMA`），不切入 node 内部层。
- 若 node 级 child 仍重叠，或该 CPU 在本 level 无域，则保留原候选（避免丢覆盖）。

例：环形四节点 NUMA-2 上 Node-0 的 group 由 `{0-1,3},{1-3}` 变为 `{0-1,3},{2}`，每个 CPU 恰好贡献一次，remote source group 不再包含共享 CPU。

## 版本演进与当前进展
*current_version: v1（RFC）*（`<tencent_3A95EEAE75A6E08A5DB20A9A6610AA4B0B09@qq.com>`）。当日发出，暂无 review。

## Maintainer 意见与讨论焦点
暂无维护者/资深成员回帖。作者声明此前对 `build_overlap_sched_groups()` 有相应学识（引用了 `group_balance_cpu()` 附近大段注释原文并逐处标注改动），但这些注释由历史作者维护，本补丁尚无任何外部确认。`Assisted-by: LLM` 标注与「未测工作负载/放置影响」是当前最需要 reviewer 审视的两点。

## 合入评估
*likelihood=unknown*。RFC 单补丁、零 review；方案方向（减少 NUMA group 重叠、修正域平均偏差）合理，但涉及负载均衡核心拓扑构建路径，且作者明确未测端到端性能与 fork 放置影响。*blocking_issues*：无 review；缺乏工作负载实测数据；改动落在 `build_overlap_sched_groups()` 这一历史敏感代码。*next_action*：先要有 reviewer 确认「收缩到子域」策略在各类拓扑下不引入漏覆盖，再补性能数据。

## 效果评估
作者仅做功能性验证：QEMU/KVM + `-numa node`/`-numa dist` 灌输六类对称 fixture（12 节点拓扑、8 节点 EPYC 风格拓扑单/交错 CPU、四节点环形、非等深拓扑），解析 `sched_verbose` 输出确认 group mask 无重叠覆盖每个域；**350 个域全部通过、EPYC group mask 不变**；另有非对称 SLIT 保证完整覆盖。userspace harness 用 UBSan 锻炼畸形跨节点 SMT。**未测工作负载性能与 fork 放置影响**（作者明确声明）。

## 我可以参与的点
- *kind: review*：核对「只下沉 NUMA 子域、不切入 node 内部」的边界条件，确认收缩不会在非对称拓扑下丢覆盖。
- *kind: testing*：在环形/非对称 SLIT 的真实 NUMA 硬件上测负载均衡后的 CPU 利用率分布与 fork 放置，量化偏差修正的实际收益。

## 参考链接
- patch: https://lore.kernel.org/all/tencent_3A95EEAE75A6E08A5DB20A9A6610AA4B0B09@qq.com/
