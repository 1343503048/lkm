# sched/cache: Remove the old cache group footprint on exec

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261009-007 → sched-20261014-010：Jemmy Wong 修 `sched_cache_exec_mmap()` 记账遗漏——exec 换 cache group 后旧 group 的 footprint 只在 exit 路径减；多轮演进确定 footprint 转 `atomic_long_t`、去 clamp、placement pass 只更新一次。
- sched-20261015-017：Chen Yu 认可改名并请作者发正式版，Jemmy 发 v3。
- sched-20261021-011：Chen Yu 在多 LLC per node 的 Xeon 上跑完整 hackbench 后给 Reviewed-by + Tested-by。
- sched-20261022-010：作者发 v4——纳入 Chen Yu 的 Reviewed-by/Tested-by、压缩提交描述；Chen Yu 回「looks good to me」。本系列带 `Fixes: b636fef85bda`。
- sched-20261109-016（今天）：**Jemmy 向 Ingo/Peter 友好 ping 请求收取 v4**；Chen Yu 提出把他的补丁并入自己的 v2 prctl 系列（带 authorship），Jemmy 同意。

## 背景与问题

（承接 sched-20261009-007 → sched-20261022-010）`sched_cache_exec_mmap()` 在 exec 时替换 cache group 后，旧 group 的 footprint 只在 exit 路径递减，导致 cache 感知聚合的 footprint 记账遗漏。v4 已收敛：footprint 转 `atomic_long_t`、去 clamp、placement pass 只更新一次、`sched_cache_replace_grp()` 改名 `sched_cache_switch_grp()`，并带 Chen Yu 的 Reviewed-by + Tested-by。今日讨论转向「该补丁如何被收取」——可能并入 Chen Yu 的 prctl 系列而非独立收取。

## 技术方案

今日无新代码。讨论结论：Chen Yu 提出把 Jemmy 的补丁（带修改、保留 authorship）并入其 v2 prctl 系列——因为 prctl 引入后需处理多处竞态，其中就包括本补丁修的 footprint 竞态；Jemmy 同意「please feel free to include my patch in your v2 prctl series with the necessary modifications」。这意味着该补丁的合入路径从「独立收取」转为「并入 Chen Yu 系列」。

## 版本演进与当前进展

*current_version: v4（2026-10-22 发出）*。今日：Jemmy 向 Ingo/Peter 友好 ping（v4 已带 Chen Yu Reviewed-by + Tested-by，仅更新注释与提交描述）；Chen Yu 提议并入其 prctl v2 系列，Jemmy 同意。

## Maintainer 意见与讨论焦点

- **Chen Yu**：提出把本补丁并入其 v2 prctl 系列（带 authorship），理由是 prctl 引入后需一并处理 footprint 等多处竞态。Jemmy 同意。
- 无 NAK。无当日 Ingo/Peter 回帖。

## 合入评估

*likelihood=high*（对「补丁最终进主线」而言，经 Chen Yu 系列）。修复本身已获 Chen Yu Reviewed-by + Tested-by 且带 Fixes 标签；今日确定并入 Chen Yu 的 prctl 系列，合入路径清晰。*blocking_issues*：① 依赖 Chen Yu prctl 系列的推进节奏；② Ingo/Peter 尚未表态。*next_action*：Chen Yu 在 prctl v2 系列中带 authorship 嵌入本补丁。

## 效果评估

无量化数据；属 cache 感知聚合 footprint 记账正确性修复（`Fixes: b636fef85bda`），Chen Yu 在多 LLC per node Xeon 上 hackbench 无超方差差异。

## 我可以参与的点

- **review**：审查 Chen Yu prctl 系列嵌入本补丁后，footprint 竞态修复与 prctl 新路径的交互是否完整。
- **testing**：在多 LLC per node 平台回归 exec 换 cache group 后的 footprint 记账。

## 参考链接

- Jemmy 的 ping: https://lore.kernel.org/all/35237F63-C205-4AE5-87C2-BE85604055C6@gmail.com/
- Chen Yu 的并入提议: https://lore.kernel.org/all/5c912bd3-8701-4395-a118-4ee6e09233e2@intel.com/

---
id: sched-20261109-016
date: '2026-11-09'
subject: "sched/cache: Remove the old cache group footprint on exec"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<35237F63-C205-4AE5-87C2-BE85604055C6@gmail.com>"
lore_url: "https://lore.kernel.org/all/35237F63-C205-4AE5-87C2-BE85604055C6@gmail.com/"
authors: [Jemmy Wong]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: null
    date: '2026-10-22'
    summary: "exec 换 cache group 后旧 group footprint 记账修复，转 atomic_long_t、去 clamp"
    review_outcome: "Chen Yu Reviewed-by + Tested-by，提议并入其 prctl 系列，Jemmy 同意"
upstream_commit: null
fixes_commit: "b636fef85bda"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "依赖 Chen Yu prctl 系列的推进节奏"
  next_action: "Chen Yu 在 prctl v2 系列中带 authorship 嵌入本补丁"
contribution_opportunities:
  - kind: review
    description: "审查 prctl 系列嵌入本补丁后 footprint 竞态修复与 prctl 新路径的交互"
  - kind: testing
    description: "在多 LLC per node 平台回归 exec 换 cache group 后的 footprint 记账"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261022-010]
tags: [load_balance, cfs, topology]
---