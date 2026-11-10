# sched_ext: Fix partial-SMT core counting in calc_shard_layout()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-007：Zhang Qiao 单独提交的 sched_ext for-7.4-fixes 补丁，修复 `calc_shard_layout()` 在 partial-SMT 系统（部分核开 SMT、部分不开）上的 core 计数错误——这是对 Tejun Heo「把修复单独发出来」要求的直接响应（放弃 `scx_cid_init()` 拆解重构、把真实 bug 独立成补丁）。
- sched-20261110-015（今天）：**v2 发出**（`sched_ext/for-7.4-fixes` 分支，内嵌 diff）。修复思路落定：core 的计数应取「该核在 `@llc_cpus` 内的第一个 sibling」而非 `topology_sibling_cpumask()` 的全局第一个 CPU——因为 sibling mask 可能包含落在其它 node/LLC 单元或已 offline 的 sibling（mips/sparc64 会把 offline sibling 留在 mask 里），导致部分核永远不被计数、`cores_per_shard` 与 `nr_large` 偏小、shard 布局不均。

## 背景与问题

（承接 sched-20261106-007）`calc_shard_layout()` 数 LLC 内的 core 数来把核均匀分摊到 shard。v1 的判定是「CPU 是 `topology_sibling_cpumask()` 的第一个 CPU 才计数」，但 `scx_cid_init()` 实际构建的 core 是「sibling mask 与 `@llc_cpus` 的交集」。sibling mask 可能包含 `@llc_cpus` 之外的 CPU——落到别的 node/LLC 的 sibling、或 mips/sparc64 这类架构上被 offline 但仍留在 mask 里的 sibling。若某核的第一个 sibling 恰是这种 CPU，该核就永远不被计数，导致 core 数偏少、shard 不均匀。

## 技术方案

v2 把计数条件从 `cpumask_first(topology_sibling_cpumask(cpu)) == cpu` 改为 `cpumask_first_and(topology_sibling_cpumask(cpu), llc_cpus) == cpu`——即在 `@llc_cpus` 内取该核第一个 sibling 作为计数点，与 `scx_cid_init()` 构建循环里「sibling ∩ llc_cpus」的 core 定义一致。`Fixes: e2c841b91bf9 ("sched_ext: Add CID sharding")`。改动 `kernel/sched/ext/cid.c` +7/-1。

## 版本演进与当前进展

*current_version: v2（2026-11-10，`<20261110091042.1805197-1-zhangqiao22@huawei.com>`）*。v1 为经 QQ 邮箱的草稿/附件形式，v2 是内嵌 diff 的正式 LKML 提交。当日无评审回复。

## Maintainer 意见与讨论焦点

当日缓存无维护者回复。补丁带 `Fixes:`、基于 for-7.4-fixes tip、属明确计数正确性修复，方向符合 Tejun 此前「把修复单独发出来」的要求。无 NAK。

## 合入评估

*likelihood=medium*。改动小、`Fixes:` 齐全、符合维护者此前的拆分要求，适合 Tejun 收取；但尚无评审。*blocking_issues*：① 需确认 `cpumask_first_and()` 在「某核无任何 sibling 落在 llc_cpus」时的语义与构建循环一致（正常应至少有自身）。*next_action*：Tejun 评审后收取到 sched_ext/for-7.4-fixes。

## 效果评估

无性能数据。价值在 shard 布局正确性（partial-SMT/跨 LLC sibling/offline sibling 场景下 core 计数不偏小、shard 均匀）。

## 我可以参与的点

- **testing**：在 partial-SMT 或「sibling 跨 node/LLC」的机器上验证 `scx_cid_init()` 的 shard 布局是否均匀、与 `calc_shard_layout()` 的 core 计数一致。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261110091042.1805197-1-zhangqiao22@huawei.com/

---
id: sched-20261110-015
date: '2026-11-10'
subject: "sched_ext: Fix partial-SMT core counting in calc_shard_layout()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261110091042.1805197-1-zhangqiao22@huawei.com>"
lore_url: "https://lore.kernel.org/all/20261110091042.1805197-1-zhangqiao22@huawei.com/"
authors: [Zhang Qiao]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: "<20261110091042.1805197-1-zhangqiao22@huawei.com>"
    date: '2026-11-10'
    summary: "core 计数改用 cpumask_first_and(sibling, llc_cpus) 与构建循环一致"
    review_outcome: "当日无评审回复"
upstream_commit: null
fixes_commit: "e2c841b91bf9"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "cpumask_first_and 在无 sibling 落在 llc_cpus 时的语义需与构建循环确认一致"
  next_action: "Tejun 评审后收取到 sched_ext/for-7.4-fixes"
contribution_opportunities:
  - kind: testing
    description: "在 partial-SMT 或 sibling 跨 node/LLC 的机器验证 shard 布局均匀且与计数一致"
generated_at: "2026-11-11T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261106-007]
tags: [sched_ext]
---