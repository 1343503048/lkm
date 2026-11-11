---
id: sched-20261111-017
date: '2026-11-11'
subject: 'sched_ext: Fix partial-SMT core counting in calc_shard_layout()'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261110091042.1805197-1-zhangqiao22@huawei.com>
lore_url: https://lore.kernel.org/all/20261110091042.1805197-1-zhangqiao22@huawei.com/
authors:
- Zhang Qiao
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v2
  msgid: <20261110091042.1805197-1-zhangqiao22@huawei.com>
  date: '2026-11-10'
  summary: core 计数改为在 llc_cpus 内取第一个 sibling
  review_outcome: Tejun Heo 已应用
upstream_commit: null
fixes_commit: e2c841b91bf9
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 7.4 修复批次进入 mainline
contribution_opportunities: []
generated_at: '2026-11-12T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261106-007
- sched-20261110-015
tags:
- sched_ext
- hyperthreading
title: 'sched_ext: Fix partial-SMT core counting in calc_shard_layout()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-007-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261106-007</a>：Zhang Qiao 提交的 sched_ext for-7.4-fixes 补丁（v1），修复 `calc_shard_layout()` 在 partial-SMT 系统（部分核开 SMT、部分不开）上的 core 计数错误——把真实 bug 独立成补丁、放弃 `scx_cid_init()` 拆解重构。
- <a class="article-ref" href="/lkm/2026/11/10/sched-20261110-015-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261110-015</a>：v2 发出（`sched_ext/for-7.4-fixes`，内嵌 diff）——core 的计数应取「该核在 `@llc_cpus` 内的第一个 sibling」而非 `topology_sibling_cpumask()` 的全局第一个 CPU，否则 partial-SMT 下部分核永远不被计数、shard 布局不均。
- <a class="article-ref" href="/lkm/2026/11/11/sched-20261111-017-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261111-017</a>（今天）：**Tejun Heo 已应用**——「Applied to sched_ext/for-7.4-fixes. Thanks.」，v2 进入 sched_ext 的 7.4 修复分支。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-007-sched-ext-fix-partial-smt-core-counting-in-calc-shard-layout.html">sched-20261106-007</a> / 20261110-015）`calc_shard_layout()` 数 LLC 内 core 数来把核均匀分摊到 shard。v1 判定「CPU 是 `topology_sibling_cpumask()` 的第一个 CPU 才计数」，但 `scx_cid_init()` 实际构建的 core 是「sibling mask 与 `@llc_cpus` 的交集」；sibling mask 可能包含 `@llc_cpus` 之外的 CPU（落入别的 node/LLC 的 sibling、或 mips/sparc64 上 offline 但仍留在 mask 里的 sibling），导致部分核永远不被计数、`cores_per_shard` 与 `nr_large` 偏小、shard 布局不均。

## 技术方案

v2 把计数条件从 `cpumask_first(topology_sibling_cpumask(cpu)) == cpu` 改为 `cpumask_first_and(topology_sibling_cpumask(cpu), llc_cpus) == cpu`——在 `@llc_cpus` 内取该核第一个 sibling 作计数点，与 `scx_cid_init()` 的 core 定义一致。`Fixes: e2c841b91bf9 ("sched_ext: Add CID sharding")`，改动 `kernel/sched/ext/cid.c` +7/-1。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<20261110091042.1805197-1-zhangqiao22@huawei.com>`）*。今日 Tejun 应用并致谢，无后续版本必要。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：已应用（`sched_ext/for-7.4-fixes`），无异议。

## 合入评估

*likelihood=merged*。已进入 `sched_ext/for-7.4-fixes` 分支。*blocking_issues*：无。*next_action*：随 7.4 修复批次进入 mainline（或相应 stable）。

## 效果评估

本补丁修复 partial-SMT 系统上 shard 布局不均（core 计数偏少）的正确性问题，作者未给量化数据。

## 我可以参与的点

当前阶段已合入维护者分支，暂无明显参与空间，可持续观察是否随 7.4 发布进入 mainline。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110091042.1805197-1-zhangqiao22@huawei.com/
- Tejun 应用确认: https://lore.kernel.org/all/601db1ca092888f567aa98806ad47de9@kernel.org/
