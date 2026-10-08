---
id: sched-20261008-001
subject: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
date: '2026-10-08'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
authors:
- Mete Durlu
maintainers_involved:
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>
  date: '2026-10-08'
  summary: RFC：SCHED_IDLE_SMT_PRIO 静态分支 + arch_needs_idle_smt_prio() 钩子，s390 启用
  review_outcome: Andrea/Shrikanth 建议复用 cpu_preferred_mask 做 soft preference，路线未收敛
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 实现路线未定：独立静态分支 vs 复用 cpu_preferred_mask soft preference
  - 与既有 asym-SMT 优先工作（25a32e400a14、Tim Chen 系列）需要对齐
  - 无跨平台收益数据
  next_action: 回应 Andrea/Shrikanth，确定路线并补收益数据后发 v2
contribution_opportunities:
- kind: review
  description: 权衡 soft preference vs 独立静态分支两条路线的合入阻力
- kind: discussion
  description: 分析 find_new_ilb 是否需要感知 preferred CPU 状态
- kind: testing
  description: x86/arm64 非对称容量+SMT 平台上实测负载打包与邻分区噪声影响
generated_at: '2026-10-09T01:00:00'
source_email_count: 7
related_articles: []
tags:
- cfs
- topology
title: 'sched: Introduce idle SMT priority for asymmetric capacity systems'
layout: article
---

## TL;DR

Mete Durlu（IBM/s390）发 RFC：在非对称容量 + SMT 的系统上，调度器目前「宁可整核空闲，也不去占忙碌高容量核的空闲 SMT 兄弟线程」，导致任务被摆到低容量空闲核上。系列引入 `SCHED_IDLE_SMT_PRIO` 配置与 `sched_idle_smt_prio` 静态分支，允许架构（先在 s390 落地）覆盖这一偏好、优先把负载打包到高容量核。当日 Andrea Righi 与 Shrikanth Hegde 都提出「更应扩展 Shrikanth 既有的 `cpu_preferred_mask` 基础设施做 soft preference」，路线尚未收敛，属早期 RFC。

## 背景与问题

调度器持续往「优先整核空闲、避免 SMT 惩罚」方向演进，特别是 commit `25a32e400a14`（"sched/fair: Prefer fully-idle SMT cores in asym-capacity idle selection"）打破了 s390 依赖的行为：s390 的 CPU capacity 代表 hypervisor 分配的运行时 entitlement（垂直极化），当整机（含逻辑分区）接近满载时，忙碌高容量核的空闲 SMT 兄弟线程开始胜过完全空闲的低容量核。把负载聚集到高容量核，能让共享更激进的低容量核保持更久空闲，减少对邻分区的噪声、提升整体性能。现有逻辑却不考虑这种「低容量核应被规避」的虚拟化平台。

## 技术方案

- `kernel/sched`（patch 1）：引入 `SCHED_IDLE_SMT_PRIO` 配置项与 `sched_idle_smt_prio` 静态分支；架构通过 select `ARCH_SUPPORTS_SCHED_IDLE_SMT_PRIO` 并实现 `arch_needs_idle_smt_prio()` 来选择启用（该钩子在每次 `asym_cpu_capacity_scan()` 中调用，若无非对称容量则静态分支被关闭）。启用后，忙碌核的空闲 SMT 兄弟线程被当作普通候选参与 idle 选择。静态分支默认 false、逐架构 opt-in，未勾选的系统行为不变。
- `s390`（patch 2）：在硬件支持拓扑（hardware-backed topology）时实现 `arch_needs_idle_smt_prio()` 打开该静态分支。
- 备选/争议路线：Andrea Righi 建议不要另起炉灶，而是基于 Shrikanth 的 `cpu_preferred_mask` 基础设施做「soft preference」——允许任务在 preferred 核无空闲线程时 spill 到其它核（sched_ext 的 scx_cosmos 已有类似机制），并按「全空闲 preferred 核 → preferred 核上的空闲 SMT 线程 → 非 preferred 核」有序搜索；他指出本系列丢掉了「全空闲 vs 部分空闲 preferred 核」这一层区分。Shrikanth 则指出他此前的 `cpu_preferred_mask` 里 `find_new_ilb()` 并不感知 preferred 状态（他尝试过改为挑 preferred CPU 做 idle load balance，但实测无显著收益、代码复杂，未做）。

## 版本演进与当前进展

v1（RFC，当日首发，`<20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com>`）。当日即有 Andrea Righi、Shrikanth Hegde 的实质 review，Mete 回应并询问「是否值得扩展 Shrikanth 现有实现」。尚无 mainline 调度维护者（Peter/Vincent/Ingo）表态。

## Maintainer 意见与讨论焦点

尚未有 mainline sched 维护者回应；实质性意见来自两位资深 sched 开发者（Andrea Righi 为 sched_ext 联合维护者）：

- **Andrea Righi**：肯定方向，但质疑实现方式——主张复用 `cpu_preferred_mask` 表达「soft preference」，保留「全空闲 preferred 核优先于部分空闲 preferred 核」的区分，并与 steal governor 的强用法共存。
- **Shrikanth Hegde**：① 指出物理 CPU 竞争下 vCPU contention 本质是超售，标记 non-preferred 已能规避低容量核；② 关切 `find_new_ilb()` 不感知 preferred 状态——若负载均衡在 non-preferred 核上发起，是否仍会把任务拉到 non-preferred 核；③ 解释自己未改 `find_new_ilb()` 的实测理由（真实负载无显著提升 + 代码复杂）。
- **Mete Durlu**：解释 s390 在 steal-time 阈值越过后才降容量，认为「是否优先 SMT」应随竞争水平动态可调，最坏情况下仍可通过标记 non-preferred 规避低容量核；倾向先打包 preferred 核、竞争压力增大再疏散 non-preferred 核。

分歧核心：独立静态分支 vs 扩展既有 `cpu_preferred_mask` 做 soft preference，以及「全空闲 vs 部分空闲」这一层区分是否必须保留。

## 合入评估

*likelihood=unknown*。此为早期 RFC、无 mainline 维护者裁决，且实现路线（独立 `SCHED_IDLE_SMT_PRIO` vs 复用 `cpu_preferred_mask` soft preference）尚未收敛。*blocking_issues*：① 需与既有 asym-SMT 优先工作（`25a32e400a14`、Tim Chen 系列的 idle 选择、Shrikanth 的 `cpu_preferred_mask`/steal governor）对齐，避免另造一套偏好机制；② Andrea 提出的「全空闲 preferred 核应优先于部分空闲 preferred 核」尚未解决；③ 无任何 cross-platform 收益数据。*next_action*：作者回应 Andrea/Shrikanth，明确走「扩展 `cpu_preferred_mask`」还是「独立静态分支」路线，并补 s390 之外的收益/噪声数据后发 v2。

## 效果评估

作者未附 benchmark 数据（RFC 阶段，仅定性论证）。可引用的间接经验来自 Shrikanth：他此前尝试让 `find_new_ilb()` 优先挑 preferred CPU 时，真实负载下未见显著提升——属个人经验判断、非本补丁数据。本补丁本身的性能/隔离收益尚无数字支撑，需标注为「主观判断，未见测试数据」。

## 我可以参与的点

- `review`：对「soft preference 扩展 `cpu_preferred_mask` vs 独立静态分支」两条路线的合入阻力、与 `have_capacity`/asym packing 交互给出权衡分析。
- `discussion`：`find_new_ilb()` 是否需要感知 preferred CPU 状态（Shrikanth 已给出一手经验），可补充触发链上的反例或简化思路。
- `testing`：在 x86/arm64 的非对称容量 + SMT 平台上实测开启该逻辑对「负载打包 + 邻分区噪声」的影响——当前最缺的就是 s390 之外的实测数据。

## 参考链接

- 系列封面: https://lore.kernel.org/all/20261008-hiperdispatchfix-v1-0-73fe41081070@linux.ibm.com/
- Andrea Righi 回复: https://lore.kernel.org/all/aseIPhrDGCYFtJNE@gpd4/
- Shrikanth Hegde 回复: https://lore.kernel.org/all/90454932-1d82-450a-ac4c-499acdedb9d7@linux.ibm.com/
