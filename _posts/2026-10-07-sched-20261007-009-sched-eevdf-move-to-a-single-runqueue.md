---
id: sched-20261007-009
date: '2026-10-07'
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: <bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>
lore_url: https://lore.kernel.org/all/d9f31316-38fb-4841-9050-8a9f3a042847@arm.com/
authors:
- Aishwarya Rambhadran
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 跨负载点行为差异尚无机制级解释
  next_action: 等「预期后果 vs 可避免回退」的裁定；细化 m/t 负载点扫描
generated_at: '2026-10-08T01:00:00'
contribution_opportunities:
- kind: testing
  detail: 非 Graviton3 平台复跑同一矩阵验证普适性
- kind: discussion
  detail: 用 WA_WEIGHT 收益翻转模型统一解释两种相反恢复模式
source_email_count: 1
related_articles:
- sched-20260923-001
- sched-20260924-009
- sched-20260928-008
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

> **subject**：`sched/eevdf: Move to a single runqueue`
> 本文为增量更新，完整脉络见下。

## TL;DR

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>：Aishwarya Rambhadran（ARM）在 AWS Graviton3 上报告个别 schbench 线程配置 p99 回退（~30%），bisect 指向单运行队列 commit（[PATCH v3 7/7] sched/eevdf: Move to a single runqueue）。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>：怀疑点收敛到 WA_WEIGHT/task_h_load，社区提议试 `NO_WA_WEIGHT` 与 `cgroup_mode` 两种规避。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20260928-008</a>：Chen Yu 纠正自己此前判断——WA_WEIGHT 在 netperf（内存带宽饱和）下其实**有帮助**，关掉它只是让 smp/concur 都掉到同一差水平、让回归「看起来消失」；规律是「带宽饱和时 waker/wakee 叠同 CPU 有收益、不饱和时有害」。倾向认为该「回归」可能是 flat cgroup task-pick 的预期后果。
- <a class="article-ref" href="/lkm/2026/10/07/sched-20261007-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20261007-009</a>（今天）：Aishwarya 交出两种规避的**对照数据**（v7.3-rc4、20 次重复 × 2 boot）——原始 bisected 的 m:16 t:16 场景 `NO_WA_WEIGHT` **无实质改善**（958541 vs 969557）、`cgroup_mode=smp` **恢复大部分**（723098，接近 v7.2 的 662869）；m:64 t:4 则相反，`NO_WA_WEIGHT` 几乎完全恢复（740454 vs v7.2 的 730453）、smp 只部分恢复；rc4 本来改善的 m:32 t:4 在 `NO_WA_WEIGHT` 下保持改善、在 smp 下消失。结论：**不是 WA_WEIGHT 单一原因**，表现为随负载配置与权重计算方式变化的负载依赖行为；开放问题——这种跨负载点的差异是新权重计算的**预期后果**，还是仍有空间避免大的 p99 回退。

## 背景与问题

（承接链上文章）EEVDF 单运行队列把层级公平/cgroup 的 task-pick 拍平后，schbench 部分线程配置出现 p99 尾延迟回退；定位史：bisect → 单 rq commit（0923）→ 怀疑 WA_WEIGHT（0924）→ Chen Yu 证明 WA_WEIGHT 在带宽饱和时是收益、NO_WA_WEIGHT 只是掩盖（0928）。今天的数据把「掩盖」这个判断做实并细化：两种规避在不同负载点上呈现**相反的恢复模式**，说明回归不是单一机制（WA_WEIGHT）而是权重计算影响下的负载依赖行为。

## 技术方案

（承接）定位/规避而非补丁。今天测试的两个旋钮：

1. `echo NO_WA_WEIGHT > /sys/kernel/debug/sched/features`——关闭 wake affine 权重；
2. `echo smp > /sys/kernel/debug/sched/cgroup_mode`——切回 SMP 模式 cgroup 调度。

schbench 请求延迟 p99（usec，越小越好；v7.3-rc4，20 重复 × 2 boot 会话）：

| 配置 | v7.2 | v7.3-rc4 | NO_WA_WEIGHT | smp |
|---|---|---|---|---|
| m:16 t:16（原始 bisected） | 662869 | 969557 | 958541 | **723098** |
| m:64 t:4 | 730453 | 942251 | **740454** | 818483 |
| m:32 t:4（rc4 改善项） | 74251 | 56725 | 59008 | 82053 |

读法：m:16 t:16 上 smp 恢复大部分（与 Prateek 此前「旧权重计算更接近层级 pick」的观察一致）；m:64 t:4 上 NO_WA_WEIGHT 几乎全恢复、smp 仅部分；m:32 t:4 的 rc4 改善在 NO_WA_WEIGHT 下保留、在 smp 下消失——两种规避各有各的负载点。

## 版本演进与当前进展

- 09-23 报告（<a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>）→ 09-24 收敛怀疑点（<a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>）→ 09-28 WA_WEIGHT 受益性反转（<a class="article-ref" href="/lkm/2026/09/28/sched-20260928-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20260928-008</a>）。
- 10-07：两种规避的对照数据落地，排除「WA_WEIGHT 单一原因」假说；提出开放问题（预期后果 vs 可避免回退）。
- 仍无补丁、无 maintainer 收取动作；regzbot 状态未见更新。

## Maintainer 意见与讨论焦点

当日无维护者回帖。Aishwarya 的数据回应的是链上社区（Chen Yu、Mike Galbraith、Prateek 等）此前的建议与观察，焦点从「谁是元凶」转为「负载依赖的差异是否是新权重计算的预期行为，以及大的 p99 回退能否避免」——这个问题直接决定该 regression 会被标记 wontfix（预期行为）还是需要补丁（可避免）。

## 合入评估

*likelihood=unknown*（本链是回归定位讨论，无补丁可合）。走向取决于开放问题的答案：若确认预期行为则关单，若认定可避免则催生权重计算补丁。*blocking_issues*：跨负载点的行为差异尚无机制级解释。*next_action*：等 Peter/Vincent 等对「预期后果 vs 可避免」的裁定；可主动做的下一步是固定负载点扫描（m/t 维度细化）找出恢复模式切换的边界。

## 效果评估

数据见技术方案表——这是本链目前最系统的对照数据集（20 重复 × 2 boot、三个负载点 × 四种配置）。定性结论两条：① NO_WA_WEIGHT 与 smp 的恢复模式在不同负载点**互补且互斥**；② m:16 t:16 的大恢复与 Prateek 的「旧权重≈层级 pick」观察自洽。

## 我可以参与的点

- `testing`：在非 Graviton3 平台（x86 大核数、不同 LLC 拓扑）复跑同一矩阵，验证恢复模式是否平台无关——决定结论的普适性。
- `discussion`：对开放问题给出机制级分析——用 WA_WEIGHT 在「带宽饱和/不饱和」下的收益翻转（Chen Yu 0928 结论）解释 m:64 t:4 与 m:16 t:16 的相反恢复模式，把两个观察统一成一个模型；这是把讨论从数据堆推进到结论的最短路径。
- 回合视角：无补丁，不适用。

## 参考链接

- Aishwarya 的对照数据: https://lore.kernel.org/all/d9f31316-38fb-4841-9050-8a9f3a042847@arm.com/
- 相关文章：<a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>（报告）、<a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>（怀疑收敛）、<a class="article-ref" href="/lkm/2026/09/28/sched-20260928-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20260928-008</a>（WA_WEIGHT 受益性反转）
