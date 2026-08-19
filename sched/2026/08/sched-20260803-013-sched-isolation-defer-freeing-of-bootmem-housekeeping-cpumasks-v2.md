# sched/isolation: Defer freeing of the bootmem housekeeping cpumasks

# sched/isolation: 推迟释放 bootmem housekeeping cpumask（释放时机细化）


## TL;DR
`sched/isolation` 推迟释放 bootmem housekeeping cpumask（08-02 系列 001）在 08-03 进入释放时机的讨论：应将释放推迟到 bootmem 回收阶段而非即刻 `memblock_free`。低严重度，合入可能性高。

## 背景与问题
`housekeeping` 初始化时用 memblock 动态分配 housekeeping cpumask。当前实现获取永久存储后立即 `memblock_free()` 掉临时 bootmem 分配。但若 early boot 某些路径在释放后仍引用该掩码（或释放时机早于 memblock 正式回收），可能访问到处于不确定状态的 memory。08-02 文章（sched-20260802-001）已覆盖 v1 的「推迟释放」方向。

## 技术方案
08-03 Mike Galbraith 的讨论进一步细化释放时机：不应在获得永久副本后即刻 `memblock_free()`，而应将 bootmem 分配的 cpumask **推迟到 bootmem 退出、memblock 统一回收阶段**再释放，确保 early 阶段所有潜在引用者都已完成访问。

## 版本演进与当前进展
- 08-02：v1 提出推迟释放（sched-20260802-001）。
- 08-03：Mike Galbraith 在 16216 回帖，细化释放时机为「推迟到 bootmem 回收阶段」。

## Maintainer 意见与讨论焦点
Mike Galbraith（reviewer）：聚焦释放时机正确性，无 NAK。与 Frederic Weisbecker / Peter Zijlstra 的 housekeeping 维护方向一致。

## 合入评估
合入可能性 high。纯释放时机修正，无功能风险，低严重度。

## 效果评估
邮件未给基准；属生命周期正确性修正。无量化数据，也不应有运行时影响。

## 我可以参与的点
- 审计 housekeeping cpumask 在 early boot 各阶段的引用点，确认推迟释放不会让任何 early 路径访问未分配内存，回帖引用点清单参与 review。

## 参考链接
- 08-02 文章：sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks
- lore thread: 未获取到

---
subject: "sched/isolation: Defer freeing of the bootmem housekeeping cpumasks"
id: sched-20260803-013
date: 2026-08-03
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260801000000.0000000-1-isolation@kernel.org>"
lore_url: "unknown"
authors: [Mike Galbraith]
maintainers_involved: [Peter Zijlstra, Frederic Weisbecker]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20260801000000.0000000-1-isolation@kernel.org>"
    date: 2026-08-02
    summary: "housekeeping 初始化用 memblock 分配 cpumask，当前直接用 memblock_free 释放；但该释放时机不对，应在 bootmem 退出后统一回收。v1 已发（sched-20260802-001）。"
    review_outcome: "08-02 已覆盖（系列 sched-20260802-001）。"
  - version: v2
    msgid: "<unknown>"
    date: 2026-08-03
    summary: "Mike Galbraith 在 08-03 回帖讨论释放时机的正确性：应将 bootmem 分配的 cpumask 推迟到 memblock 释放阶段（而非立即 memblock_free），避免 early 阶段仍引用该掩码时访问已释放内存。"
    review_outcome: "讨论聚焦释放时机（memblock_free 即刻 vs 推迟到 bootmem 回收）；无 NAK。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["需确认释放时机与 memblock 回收阶段的精确对齐"]
  next_action: "等待作者确认采用『推迟到 bootmem 退出』的释放点，发 v2 定稿。"
contribution_opportunities:
  - kind: review
    description: "可审阅 housekeeping cpumask 在 early boot 各阶段的引用点，确认推迟释放不会让任何 early 路径访问到未分配内存，回帖引用点审计。"
generated_at: "2026-08-04T00:20:00"
source_email_count: 1
related_articles: ["sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks"]
tags: [isolation, affinity]
---
