---
id: sched-20261022-009
date: 2026-10-22
subject: 'sched/topology: Balance cluster static-key updates'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261021034314.864713-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261022070526.728824-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v3
patch_series:
- version: v3
  msgid: <20261022070526.728824-1-sh_def@163.com>
  date: 2026-10-22
  summary: 合并 SD_CLUSTER 检测到 detach 循环，递减移到 detach 后，Cc stable
  review_outcome: Tim Chen 建议已吸收；K Prateek Nayak + Kayra Cizmeci Reviewed-by
upstream_commit: null
fixes_commit: 8881e1639f1f
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待维护者收取并处理 stable 回合
contribution_opportunities:
- kind: review
  description: 确认递减移到 detach 后与 lowest_flag_domain 判定的正确性
- kind: testing
  description: 在 cluster 平台验证销毁分区后 cluster-aware 调度保持使能
generated_at: '2026-10-23T01:20:00'
source_email_count: 3
related_articles:
- sched-20261021-005
tags:
- topology
- load_balance
title: 'sched/topology: Balance cluster static-key updates'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-005-sched-topology-balance-cluster-static-key-updates.html">sched-20261021-005</a>：Hui Su 发往 sched 的单补丁修复：`sched_cluster_active` static key 的增/减计数不对称——`build_sched_domains()` 每新建一个含 SD_CLUSTER 域的分区就加一次，而 `detach_destroy_domains()` 删分区时只看全局 static key 是否使能就减，导致销毁「不含 cluster 域」的分区会误减别的分区持有的引用，把 cluster-aware 调度全局关掉。v2 按 K Prateek Nayak 意见用 `sched_cluster_active` 守卫扫描，Kayra Cizmeci 追加 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-009-sched-topology-balance-cluster-static-key-updates.html">sched-20261022-009</a>（今天）：作者发 v3——按 Tim Chen 建议把 SD_CLUSTER 检测并入现有 detach 循环（省一次 CPU mask 遍历与 RCU 读侧段）、把 static-key 递减移到 detach 之后、并加 `Cc: stable@vger.kernel.org`；v3 已带 K Prateek Nayak 与 Kayra Cizmeci 双 Reviewed-by。Tim Chen 同时确认 inc/dec 确实不平衡、并建议回合 stable。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-005-sched-topology-balance-cluster-static-key-updates.html">sched-20261021-005</a>）`build_sched_domains()` 对每个含 SD_CLUSTER 域的新分区递增 `sched_cluster_active`，但 `detach_destroy_domains()` 在递减前只测试全局 static key——与「该被删分区是否真有 SD_CLUSTER 域」无关。于是删除 cluster-less 分区会误减其它 cluster 分区的引用，关掉 cluster-aware 调度。作者给出两个可复现场景：两 cluster 分区 + 删 singleton 分区后基线计数错降为 1（应为 2）；非对称 cluster 拓扑下基线计数错降为 0（应为 1）。今日无新背景，进展到 v3 定稿。

## 技术方案
（承接 v2）单补丁（`kernel/sched/topology.c`，v3 为 +10/-4）：`detach_destroy_domains()` 不再以「全局 key 使能」决定是否递减，而是在现有 `rcu_read_lock()` 遍历 `cpu_map` 拆除域的循环里，用 `static_branch_unlikely(&sched_cluster_active) && lowest_flag_domain(i, SD_CLUSTER)` 置 `has_cluster`；循环结束、`rcu_read_unlock()` 之后再 `if (has_cluster) static_branch_dec_cpuslocked(&sched_cluster_active)`。v3 相对 v2：并入 Tim Chen 的「合并遍历」建议（省第二次 CPU mask 遍历与 RCU 段）、递减移到 detach 之后、加 Cc stable。

## 版本演进与当前进展
*current_version: v3*（`<20261022070526.728824-1-sh_def@163.com>`）。v2: `<20261021043834.1140951-1-sh_def@163.com>`，v1: `<20261021034314.864713-1-sh_def@163.com>`。v3 已带 K Prateek Nayak、Kayra Cizmeci 双 Reviewed-by 与 `Cc: stable@vger.kernel.org`。

## Maintainer 意见与讨论焦点
Tim Chen 认可「inc/dec 确实不平衡」，建议把 SD_CLUSTER 检测并入现有 detach 循环以只做一次 rcu + cpu_map 遍历，并认为「递减移到 detach 后是安全的」（cluster 代码仍会对实际域测试 SD_CLUSTER 标志），且建议回合 stable。Hui Su 采纳并出 v3。无反对意见。

## 合入评估
*likelihood=high*。v3 已收两位 reviewer 的 Reviewed-by，方向无异议、修复有明确 Fixes 标签并提请 stable；*blocking_issues*：无实质卡点；*next_action*：等待维护者收取（并处理 stable 回合）。

## 效果评估
作者在提交信息中给出两个可复现场景的计数对比（删 singleton 分区后基线计数 1→修复后 2；非对称拓扑 0→修复后 1）；无性能数字。

## 我可以参与的点
- *kind: review*：确认 v3 把递减移到 detach 后与 `lowest_flag_domain()` 判定的正确性。
- *kind: testing*：在带 cluster 分区的平台验证销毁分区后 cluster-aware 调度仍保持使能。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261022070526.728824-1-sh_def@163.com/
- Tim Chen 今日回帖：https://lore.kernel.org/all/94773ec2c845d88b291df265935342eb1a3c9f7e.camel@linux.intel.com/
