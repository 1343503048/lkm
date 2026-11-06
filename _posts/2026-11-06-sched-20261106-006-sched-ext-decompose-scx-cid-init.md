---
id: sched-20261106-006
date: 2026-11-06
subject: 'sched_ext: Decompose scx_cid_init()'
subsystem: sched
type: feature
status: superseded
severity: none
thread_root_msgid: <20261105065013.784398-1-zhangqiao22@huawei.com>
lore_url: https://lore.kernel.org/all/20261105065013.784398-1-zhangqiao22@huawei.com/
authors:
- Zhang Qiao
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <20261105065013.784398-1-zhangqiao22@huawei.com>
  date: 2026-11-05
  summary: 4 补丁拆解 scx_cid_init() 单体，纯代码搬移。
  review_outcome: Tejun 否决重构价值，要求单独发修复。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
  - 重构价值被维护者 Tejun Heo 明确否决
  next_action: 放弃拆解，单独提交 calc_shard_layout 修复
contribution_opportunities: []
generated_at: '2026-11-07T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261105-010
tags:
- sched_ext
title: 'sched_ext: Decompose scx_cid_init()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-010-sched-ext-decompose-scx-cid-init.html">sched-20261105-010</a>：Zhang Qiao 的 4 补丁系列把 `scx_cid_init()` 约 230 行单体拆解为共享 file-private builder 结构体的若干 stage helper，纯代码搬移、无行为变化，为后续修 `calc_shard_layout()` 的 partial-SMT core 计数与单核 shard 硬上限做铺垫。
- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-006-sched-ext-decompose-scx-cid-init.html">sched-20261106-006</a>（今天）：**Tejun Heo 否决了这次重构**——「我不认为这次重构让任何事情变好，结果似乎比现在的代码更复杂……函数长本身不是自动重构的理由；`scx_cid_init()` 是一段有顺序、每步只跑一次的线性序列，拆成 single-caller helper 只是加了调用边界和一个只用来搬计数器/掩码的 builder 结构，读者反而要跳来跳去」，并明确要求「把修复单独发出来」。作者随后放弃重构系列，另行单独发出 partial-SMT 修复（见同日 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-007-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261106-007</a>）。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-010-sched-ext-decompose-scx-cid-init.html">sched-20261105-010</a>）`scx_cid_init()` 经多轮演进膨胀成约 230 行单体，把表分配、node/LLC/cluster/core 拓扑遍历、无拓扑 tail、shard 范围收尾四条逻辑交错在一起。作者原本计划先拆开该函数、再修两个真实问题（partial-SMT 核计数、单核 shard 硬上限）。Tejun 的否定表明：在维护者看来，这个函数「自上而下读下来是清晰的」，拆解收益不成立。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/11/05/sched-20261105-010-sched-ext-decompose-scx-cid-init.html">sched-20261105-010</a>）原系列四步、每步独立可编译：拆出表/掩码分配、逐 node 遍历在线 CPU、无拓扑 tail 的 CID 分配、shard 范围填充等 stage helper，共享一个 builder 结构体。Tejun 的反对集中在方法论：线性序列 + single-caller helper + 纯搬移 builder 的组合，反而增加读者的跳转成本，不是价值重构。

## 版本演进与当前进展

*current_version: v1（2026-11-05 发出）*。今日 Tejun Heo 否决重构方向，作者放弃该系列（拆解中止），转而按 Tejun「把修复单独发出来」的要求，单独提交 partial-SMT core 计数修复。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）明确否定重构价值：函数长不是自动重构的理由，拆解让结果更复杂、读者要跳来跳去，并要求「Can you please send the fixes separately?」。这是明确的 reject（针对重构本身，非针对后续修复）。

## 合入评估

*likelihood=rejected*。重构方向被维护者明确拒绝，作者已放弃。*blocking_issues*：重构价值被否决。*next_action*：不再推进拆解；改为单独提交 `calc_shard_layout()` 的 partial-SMT 修复（已发生，见 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-007-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261106-007</a>）。

## 效果评估

本系列为纯代码搬移、无行为变化，无效果数据。其价值（可读性）被维护者主观否定。

## 我可以参与的点

当前阶段暂无明显参与空间：重构已被否决、后续修复也已单独发出，可观察 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-007-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261106-007</a> 中 partial-SMT 修复的评审走向。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261105065013.784398-1-zhangqiao22@huawei.com/
- Tejun 的回帖: https://lore.kernel.org/all/08f0886ea1c48eed84bf6aadcf921530@kernel.org/
