# sched/topology: Balance cluster static-key updates

## TL;DR
Hui Su 发往 sched 的单补丁修复：`sched_cluster_active` static key 的增/减计数不对称——`build_sched_domains()` 每新建一个含 SD_CLUSTER 域的分区就加一次，而 `detach_destroy_domains()` 删分区时只看全局 static key 是否使能就减，导致销毁一个「不含 cluster 域」的分区会误减掉别的分区持有的引用，把 cluster-aware 调度全局关掉（即使 SD_CLUSTER 域仍已安装）。修复改为先检查将被拆除的域、仅当被删分区确含 SD_CLUSTER 时才减。v2 按 K Prateek Nayak 意见用 `sched_cluster_active` 守卫扫描，Kayra Cizmeci 追加 Reviewed-by。

## 背景与问题
`build_sched_domains()` 对每个含 SD_CLUSTER 域的新分区递增 `sched_cluster_active`，但 `detach_destroy_domains()` 在递减前只测试全局 static key（`static_branch_unlikely(&sched_cluster_active)`）——与「该被删分区是否真的有 SD_CLUSTER 域」无关。于是：删除一个 cluster-less 分区也会执行 `static_branch_dec`，减去其它 cluster 分区持有的引用，从而关闭 cluster-aware 调度，尽管 SD_CLUSTER 域仍然安装。作者给出两个可复现场景：两 cluster 分区 + 删 singleton 分区后基线计数错降为 1（应为 2）；非对称 cluster 拓扑下基线计数错降为 0（应为 1）。

## 技术方案
单补丁（`kernel/sched/topology.c`，v2 为 +14/-2）：
- `detach_destroy_domains()` 不再以「全局 key 使能」决定是否递减，而是 `rcu_read_lock()` 遍历被拆分区，用 `lowest_flag_domain(i, SD_CLUSTER)` 检查是否含 SD_CLUSTER 域，仅当 `has_cluster` 为真才 `static_branch_dec_cpuslocked(&sched_cluster_active)`。
- v2：把整个扫描用 `static_branch_unlikely(&sched_cluster_active)` 守卫，使无 cluster 域的系统完全跳过该循环（K Prateek Nayak 的 nit）。

## 版本演进与当前进展
*current_version: v2*。
- v1（`<20261021034314.864713-1-sh_def@163.com>`）：先扫描再递减。
- v2（`<20261021043834.1140951-1-sh_def@163.com>`）：加 `sched_cluster_active` 守卫避免无 cluster 域系统的多余循环。

## Maintainer 意见与讨论焦点
K Prateek Nayak（AMD）：一个 nit——应仅在 `sched_cluster_active` 使能时才扫描，避免无 cluster 域系统的额外循环；除此之外给出 *Reviewed-by*。Kayra Cizmeci：*Reviewed-by*（LGTM）。无分歧。

## 合入评估
*likelihood=high*。修复 static key 引用计数不对称这一明确缺陷，带 `Fixes:`，两位 reviewer 均 Reviewed-by，无争议。*blocking_issues*：无。*next_action*：等 sched 维护者收取。

## 效果评估
无 benchmark 数据。属正确性修复：作者给出了两个拓扑场景下的计数对比（修复前错降、修复后正确），消除 cluster-aware 调度被误关闭的隐患。

## 我可以参与的点
当前阶段已获两位 reviewer Reviewed-by，暂无明显参与空间，可持续观察其合入。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20261021043834.1140951-1-sh_def@163.com/
- v1 patch：https://lore.kernel.org/all/20261021034314.864713-1-sh_def@163.com/
- K Prateek Nayak 评审：https://lore.kernel.org/all/62a7530f-ffe7-490e-8d0a-3bed170e24d3@amd.com/

---
id: sched-20261021-005
date: 2026-10-21
subject: "sched/topology: Balance cluster static-key updates"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261021043834.1140951-1-sh_def@163.com>"
lore_url: "https://lore.kernel.org/all/20261021043834.1140951-1-sh_def@163.com/"
authors: ["Hui Su"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261021034314.864713-1-sh_def@163.com>"
    date: 2026-10-21
    summary: "detach_destroy_domains 按安装域判断是否递减 sched_cluster_active"
    review_outcome: "K Prateek Nayak nit：应用 sched_cluster_active 守卫扫描"
  - version: v2
    msgid: "<20261021043834.1140951-1-sh_def@163.com>"
    date: 2026-10-21
    summary: "用 sched_cluster_active 守卫 SD_CLUSTER 扫描"
    review_outcome: "K Prateek Nayak 与 Kayra 均 Reviewed-by"
upstream_commit: null
fixes_commit: "8881e1639f1f"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "等 sched 维护者收取"
contribution_opportunities: []
generated_at: "2026-10-22T01:30:00"
source_email_count: 5
related_articles: []
tags: [topology, load_balance]
---