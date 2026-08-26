---
id: sched-20260826-002
date: 2026-08-26
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: unknown
lore_url: https://lore.kernel.org/lkml/20260824125223.508178-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- K Prateek Nayak
current_version: v2
patch_series:
- version: v1
  msgid: unknown
  date: 2026-08-24
  summary: 首发 2 篇清理补丁，减少 enqueue_task_fair() 中的重复计算
  review_outcome: Prateek 提出变量命名 nit
- version: v2
  msgid: unknown
  date: 2026-08-26
  summary: Patch 2/2 增加 (is_curr || curr->on_rq) 条件保护 curr_weight
  review_outcome: 等待对命名建议的回应
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 变量命名需要改进
  next_action: 回应 Prateek 命名建议后发 v3
contribution_opportunities: []
generated_at: '2026-08-27T01:12:00'
source_email_count: 4
related_articles: []
tags:
- cfs
title: 'sched/fair: reduce repeated work in enqueue path'
layout: article
---

## TL;DR

Kayra Cizmeci 提交了 v2 版本的 2 篇清理补丁，减少 `enqueue_task_fair()` 中的重复计算：将 `ENQUEUE_DELAYED` 检查集中为一个 bool，并将 `curr == se` 的判断结果传递给 `place_entity()` 和 `requeue_delayed_entity()` 避免重复计算。K Prateek Nayak 对变量命名提出了 nit。属于代码清理，无功能变更。

## 背景与问题

`enqueue_task_fair()` 中，`flags & ENQUEUE_DELAYED` 的检查分散在多处，`cfs_rq->curr == se` 的判断也在 `place_entity()` 和 `requeue_delayed_entity()` 中各自独立计算。虽然编译器可能优化掉重复计算，但代码可读性和维护性可以改进。

## 技术方案

- **Patch 1/2**：在 `enqueue_task_fair()` 开头计算 `bool delayed = (flags & ENQUEUE_DELAYED)`，后续所有检查统一使用 `delayed`
- **Patch 2/2**：将 `enqueue_task_fair()` 中已计算的 `curr == se` 结果作为参数传递给 `place_entity()` 和 `requeue_delayed_entity()`，避免重复查找。同时添加 `(is_curr || curr->on_rq)` 条件确保 `curr_weight` 不被浪费

v2 相对 v1 的改动：Patch 2/2 新增了 `curr_weight` 的条件保护。

## 版本演进与当前进展

- v1（2026-08-24）：首发
- v2（2026-08-26）：Patch 2/2 增加 `(is_curr || curr->on_rq)` 条件

K Prateek Nayak 对 Patch 1/2 提出命名 nit：`bool delayed` 配合 `!p->se.sched_delayed || delayed` 读起来矛盾（"not delayed or delayed?"），建议改为 `wakeup_delayed` 或保留原始的 `ENQUEUE_DELAYED`。

## Maintainer 意见与讨论焦点

K Prateek Nayak 的 review 较为温和，仅提出命名建议，未对方案本身提出异议。这表明方向被认可，但变量命名需要改进以提高可读性。

## 合入评估

- **likelihood**: medium（纯清理，方向被认可，需要回应命名 nit 后发 v3）
- **blocking_issues**: 变量命名需要改进
- **next_action**: 回应 Prateek 的命名建议，发 v3

## 效果评估

作者在 x86 (Zen 3) 上用 `perf bench sched messaging`（200 groups, 5000 loops）测试，结果"good"但承认 booted with busybox，测试窗口内负载较轻。暂无有说服力的性能数据。

## 我可以参与的点

- 可以在更重的负载下跑 benchmark 验证清理是否真的无性能影响
- Patch 2/2 添加的 `WARN_ON_ONCE(curr != new_calc_curr)` 值得在更多架构上测试

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260824125223.508178-1-kayracizmeci@gmail.com/
