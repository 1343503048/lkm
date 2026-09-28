---
id: sched-20260928-008
date: '2026-09-28'
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: regression
status: under_review
severity: medium
thread_root_msgid: <bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com>
lore_url: https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/
authors:
- Aishwarya Rambhadran
maintainers_involved:
- Chen Yu
- Mike Galbraith
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - WA_WEIGHT 在带宽饱和/不饱和下的行为差异需数据坐实
  - 需 Peter Zijlstra 对是否预期取舍定性
  next_action: Chen Yu 补数据，Peter 定性
contribution_opportunities:
- kind: testing
  description: 不同内存带宽下复测 waker/wakee 叠放对 schbench p99/netperf 的影响
- kind: discussion
  description: 就 WA_WEIGHT 纳入更多因素的设计参与讨论
generated_at: '2026-09-29T01:00:00'
source_email_count: 2
related_articles:
- sched-20260924-009
- sched-20260923-001
tags:
- eevdf
- cfs
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。这是对「sched/eevdf: Move to a single runqueue」引入的 schbench p99 延迟回归的持续定位讨论。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a>：Fastpath 在 AWS Graviton3 上报告个别 schbench 线程配置 p99 回退（~30%），bisect 指向单运行队列 commit。
- <a class="article-ref" href="/lkm/2026/09/24/sched-20260924-009-sched-eevdf-move-to-a-single-runqueue.html">sched-20260924-009</a>：怀疑点收敛到 WA_WEIGHT/task_h_load，社区提议试 `NO_WA_WEIGHT` 与 `cgroup_mode`。
- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-008-sched-eevdf-move-to-a-single-runqueue.html">sched-20260928-008</a>（今天）：Chen Yu 纠正自己此前判断——WA_WEIGHT 在 netperf 下其实**有帮助**，关掉它只是让 smp/concur 都掉到同一差水平、让回归「看起来消失」；真正的规律是「内存带宽饱和时把 waker/wakee 叠在同一 CPU 有收益，带宽不饱和时叠放有害」。Mike Galbraith 认同，并补充 waker/wakee 并发度对 post-wakeup 尾部的影响。结论倾向：该「回归」可能是 flat cgroup task-pick 的预期后果。

## 背景与问题

（承接）单运行队列拍平 EEVDF 层级后，层级公平/cgroup 配置下的 p99 尾部延迟是否与收益不对称。今天无新数据点，讨论从「WA_WEIGHT 是不是元凶」深化为「WA_WEIGHT 在什么条件下是收益、什么条件下是伤害」。

## 技术方案

（承接）定位/规避而非补丁：上一轮提出的 `NO_WA_WEIGHT` 规避被 Chen Yu 今天自我推翻（它掩盖而非解决问题）。今天的新判断是让 WA_WEIGHT 纳入更多因素（Chen Yu 原话「Maybe we need to make WA_WEIGHT consider more factors here」），但仍无具体补丁。

## 版本演进与当前进展

*current_version: null*（回归定位阶段，无新补丁）。09-28 两封回复推进了因果理解：Chen Yu 描述其测试机拓扑（2 NUMA 节点、每节点 96 核共享 L3、每 4 核共享 L2），指出「waker/wakee 同核交替运行是内存带宽饱和时最省 L2 逐出的方式」，故叠放在该条件下大幅有益；Mike Galbraith 认同并指出「box 接近饱和时，把 somewhat synchronous 的负载叠起来是更好的赌注」。

## Maintainer 意见与讨论焦点

- **Chen Yu（Intel）**：自我纠正——WA_WEIGHT 在 netperf 有帮助；「回归」可能是预期后果，建议 WA_WEIGHT 纳入更多因素；将收集更多数据。
- **Mike Galbraith**：认同 CPU 侧判断；waker/wakee 并发即使 modest 影响也不小，不必要的叠放会把 post-wakeup 尾巴变成对 wakee 的 CPU 服务延迟注入。
- 无 NAK；仍未见 Peter Zijlstra 对「是否预期取舍」的正式定性（这是回归定性的关键）。

## 合入评估

*likelihood=unknown*。回归仍在定位阶段：讨论倾向「预期后果」但未定论，也未形成修复方案（`NO_WA_WEIGHT` 已被作者自我否定为规避手段）。*blocking_issues*：WA_WEIGHT 在「带宽饱和 vs 不饱和」下的行为差异需数据坐实；需 Peter 定性。*next_action*：Chen Yu 承诺补更多数据；Peter 对「是否预期取舍」给出结论。

## 效果评估

- 历史数据（承接 09-23）：schbench p99 m16/t16 -31.63%、m64/t4 -22.48%、m32/t4 +30.90%，整体混合。
- 今日新增：Chen Yu 的定性观察（带宽饱和时 waker/wakee 叠放有收益、L2 miss 率更低），但未附新的量化数字。

## 我可以参与的点

- `testing`：在不同内存带宽/负载类型下复测「waker/wakee 叠放 vs 分散」对 schbench p99 与 netperf 的影响，用数据区分「带宽饱和」与「不饱和」两种区间。
- `discussion`：就「让 WA_WEIGHT 纳入更多因素」的具体设计（如何感知内存带宽压力）参与讨论或提设计草图。

## 参考链接

- Chen Yu 今日回复: https://lore.kernel.org/all/arnbKNWNIIEcQ0a-@chenyu-dev/
- Mike Galbraith 今日回复: https://lore.kernel.org/all/4d4f5fdee4d1f462ba3490a6b3921006285e7fcc.camel@gmx.de/
- 回归报告（09-23）: https://lore.kernel.org/all/bd81bbec-ee59-401a-bec6-116196ad3a34@arm.com/
