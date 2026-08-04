---
id: sched-20260804-017
date: 2026-08-04
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "unknown"
authors: [Shrikanth Hegde]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Gautham R Shenoy]
current_version: v10
patch_series:
  - version: v10
    msgid: "<unknown>"
    date: 2026-08-04
    summary: "cpu_preferred_mask 系列（v9→v10 准备）的文档化：把『preferred CPU』概念（per-task 偏好的小核/大核子集，用于节能与缓存热）写入 sched 文档。作者表示仍在等待一组 benchmark 数字以支撑最终合入。"
    review_outcome: "Gautham R Shenoy 等参与 review；作者自述『等 benchmark 数字』，尚未合入。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["作者明确表示仍缺一组支撑合入的 benchmark 数字（『waiting on a set of numbers』）"]
  next_action: "等待作者补 benchmark 数据后合入。"
contribution_opportunities:
  - kind: testing
    description: "这正是作者自述的缺口：可在大/小核异构机型上以典型负载测量 cpu_preferred_mask 带来的能效/延迟收益，回帖 benchmark 数据（作者公开请求数字）。"
generated_at: "2026-08-05T00:25:00"
source_email_count: 1
related_articles: []
tags: [docs, affinity, capacity]
---

# sched/docs: 文档化 cpu_preferred_mask（v10 准备）

## TL;DR
Shrikanth Hegde 把 `cpu_preferred_mask`（per-task 偏好的大/小核子集，用于节能与缓存热）概念文档化，作为 cpu_preferred_mask 系列（v9→v10）的一部分。作者公开表示仍在等待一组 benchmark 数字支撑合入。合入可能性 medium——明确等数据。

## 背景与问题
`cpu_preferred_mask` 是 per-task 的「偏好 CPU 子集」机制：在异构（big.LITTLE / 大小核）系统上，让任务偏向其偏好的一组 CPU，以兼顾缓存热与节能。该机制此前缺乏文档，理解与使用门槛高。

## 技术方案
本补丁把 `cpu_preferred_mask` 的语义、与 `cpu_smt_mask` / `cpu_core_mask` 的关系、以及其在 wakeup/balancing 中的使用写入 `Documentation/scheduler/` 文档。属于机制系列的文档配套（v9→v10 准备）。

## 版本演进与当前进展
当前作为 v9→v10 准备的一部分（2026-08-04）。作者 Shrikanth Hegde 自述「waiting on a set of numbers」——即缺一组支撑最终合入的 benchmark。

## Maintainer 意见与讨论焦点
Gautham R Shenoy 等参与 review。焦点是：机制本身方向认可，但需 benchmark 数字支撑合入（作者已公开承认此缺口）。

## 合入评估
合入可能性 medium。阻塞在作者补齐 benchmark 数据，无方向反对。

## 效果评估
文档补丁本身无性能影响。但系列整体合入取决于 benchmark 数字——作者未附，正是最明确的参与点。

## 我可以参与的点
- 这正是作者公开请求的缺口：在大小核异构机型上以典型负载测量 cpu_preferred_mask 的能效/延迟收益，回帖 benchmark 数据（可直接推动系列合入）。

## 参考链接
- lore thread: 未获取到
