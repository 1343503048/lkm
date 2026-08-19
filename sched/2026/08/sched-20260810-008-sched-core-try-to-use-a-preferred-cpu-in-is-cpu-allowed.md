# sched/core: Try to use a preferred CPU in is_cpu_allowed

## TL;DR
Shrikanth Rao 的 v9 11-patch「preferred CPU」系列中 PATCH 04/11 在 `is_cpu_allowed()` 尝试使用任务的 preferred CPU。Mete Durlu 在 8/10 对 preferred CPU 与 `is_cpu_allowed` 的交互给出反馈。under_review。

## 背景与问题
「preferred CPU」机制允许任务表达偏好的运行 CPU（用于 NUMA/LLC 局部性等）。但在 `is_cpu_allowed()` 这类检查任务能否放到某 CPU 的路径中，原有逻辑未考虑 preferred CPU，导致偏好与可用性约束冲突时行为不直观。

## 技术方案
PATCH 04/11 在 `is_cpu_allowed()` 中优先尝试任务的 preferred CPU：当任务因亲和性/约束受限时，先回退到 preferred CPU（若其仍允许），再回退到通用候选。设计取舍：preferred CPU 作为「软偏好」，不覆盖硬约束（cpuset/root_domain）。

## 版本演进与当前进展
当前 v9（系列 11 patches）。8/10 Mete 反馈 preferred CPU 与 `is_cpu_allowed` 边界。作者预计修订讨论点。

## Maintainer 意见与讨论焦点
Mete 关注 preferred CPU 在 `is_cpu_allowed` 中与原约束（cpuset、root_domain）的优先级顺序，以及是否会改变既有的迁移行为。

## 合入评估
合入可能性 medium。属大型系列的一部分，需整体推进。

## 效果评估
无独立 benchmark；目标是更优的局部性放置。

## 我可以参与的点
- 在 cpuset 受限场景验证 preferred CPU 不破坏硬约束；
- 评审 preferred CPU 与 is_cpu_allowed 的优先级顺序。

## 参考链接
- lore: 未获取到

---
subject: "sched/core: Try to use a preferred CPU in is_cpu_allowed"
id: sched-20260810-008
date: 2026-08-10
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260809120449.xxxxxx-shrikanth@kernel.org>"
lore_url: "未获取到"
authors: [Shrikanth Rao]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Ingo Molnar, Mete Durlu, Juri Lelli]
current_version: v9
patch_series:
  - version: v9
    msgid: "<20260809120449.xxxxxx-shrikanth@kernel.org>"
    date: 2026-08-09
    summary: "v9 11-patch 系列中的 PATCH 04/11：在 is_cpu_allowed() 中尝试使用任务的 preferred CPU（亲和性扩展），让受限任务优先留在偏好的核上。"
    review_outcome: "Mete Durlu 在 8/10 针对 preferred CPU 与 is_cpu_allowed 的交互给出反馈；讨论 preferred CPU 与 root_domain/cpuset 约束的边界。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["preferred CPU 与 cpuset/root_domain 约束的交互需澄清"]
  next_action: "等待作者回应 Mete 关于 is_cpu_allowed 边界的反馈。"
contribution_opportunities:
  - kind: review
    description: "评审 preferred CPU 在 is_cpu_allowed 中的选取逻辑与约束优先级。"
  - kind: testing
    description: "在 cpuset 受限 + preferred CPU 场景下验证任务不被错误迁移。"
generated_at: "2026-08-11T00:15:00"
source_email_count: 2
related_articles: []
tags: [sched/core, affinity]
---
