# sched/fair: EEVDF 入队路径清理——复用 ENQUEUE_DELAYED 与避免重复计算

## TL;DR
两个小补丁清理 `enqueue_task_fair()` 路径：(1) 将分散的 `flags & ENQUEUE_DELAYED` 检查统一为一个 `delayed` 布尔变量；(2) 避免 `place_entity()` 和 `requeue_delayed_entity()` 对 `curr` 状态的重复计算。无功能变更，纯代码质量改进。

## 背景与问题
`enqueue_task_fair()` 中 `flags & ENQUEUE_DELAYED` 的检查散布在多处，且在 `requeue_delayed_entity()` 和 `place_entity()` 中对 `se == curr` 的判断被重复计算。这些冗余不仅影响可读性，还可能在后续修改中引入不一致。

## 技术方案
**Patch 1/2**：在 `enqueue_task_fair()` 入口处计算 `bool delayed = flags & ENQUEUE_DELAYED`，后续统一使用该变量替代散落的位运算检查。

**Patch 2/2**：将 `cfs_rq->curr == se` 的判断从 `enqueue_task_fair()` 传递到 `requeue_delayed_entity()` 和 `place_entity()`，避免在 `place_entity()` 中对 `avg_vruntime_weight()` 的重复调用（当 `se == curr` 时）。

关键改动：
```c
// 之前：多次调用
if (se == cfs_rq->curr)
    avg_vruntime_weight(cfs_rq, ...);  // 第一次
// ... 后续又调用
avg_vruntime_weight(cfs_rq, ...);      // 重复

// 之后：传递已有的判断结果，避免重复
```

## 版本演进与当前进展
- **v1**（Kayra Cizmeci）：首发，2 个补丁

当前版本：v1，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者回复。这是纯清理补丁，不涉及功能变更，通常审查周期较短。

## 合入评估
合入可能性 **medium**：
- 纯代码清理，无功能变更
- 但涉及核心调度路径，需要维护者确认不会引入微妙差异
- `blocking_issues`：无
- `next_action`：等待 Peter Zijlstra 或 Vincent Guittot review

## 效果评估
无性能影响（声称 "No functional change intended"）；改善代码可读性和可维护性。

## 我可以参与的点
当前阶段暂无明显参与空间。如果作者需要，可以帮忙验证在不同内核配置下的编译和基本功能。

## 参考链接
- lore thread: 未获取到

---
id: sched-20260824-011
date: 2026-08-24
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<unknown>"
lore_url: "未获取到"
authors:
- Kayra Cizmeci
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v1
patch_series:
  - version: v1
    msgid: "<unknown>"
    date: 2026-08-24
    summary: "复用 ENQUEUE_DELAYED 计算，避免 curr 状态重复判断"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等待维护者 review"
contribution_opportunities: []
generated_at: "2026-08-25T10:40:00"
source_email_count: 2
related_articles: []
tags: [sched/fair, eevdf, cleanup]
---
