# sched/isolation: Defer freeing of cpumask memblock memory to initcall

## TL;DR

Waiman Long 的 v4 补丁将 `house_mask` 的 memblock 内存释放延迟到 initcall 阶段，避免早期启动问题。Waiman 在 2026-07-30 ping 询问是否可合入，但暂无回复。

## 背景与问题

当前 `house_mask` 的 memblock 内存在启动早期被释放，可能导致后续访问问题。需要将释放时机延迟到 initcall 阶段。

## 技术方案

v4 方案将 cpumask memblock 内存释放从当前位置延迟到 initcall，确保早期启动代码路径不会访问已释放的内存。

## 版本演进与当前进展

- v4 已迭代到第 4 版
- 2026-07-30: Waiman Long ping 询问 patch 状态："Is this patch in a state that is merge-able?"
- 暂无回复

## Maintainer 意见与讨论焦点

暂无明确 review 意见。Waiman 在等待 maintainer 响应。

## 合入评估

- **likelihood**: medium
- 已迭代到 v4，说明经过多轮修改
- 但 maintainer 尚未明确回应

## 效果评估

暂无效果数据。

## 我可以参与的点

当前阶段暂无明显参与空间。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260701195810.477326-1-longman@redhat.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/isolation: Defer freeing of cpumask memblock memory to initcall"
id: sched-20260730-007
date: 2026-07-30
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260701195810.477326-1-longman@redhat.com>"
lore_url: "https://lore.kernel.org/lkml/20260701195810.477326-1-longman@redhat.com"
authors: [Waiman Long]
maintainers_involved: [Waiman Long]
current_version: v4
patch_series:
  - version: v4
    msgid: "<20260701195810.477326-1-longman@redhat.com>"
    date: 2026-07-01
    summary: "Defer freeing cpumask memblock memory to initcall to avoid early boot issues"
    review_outcome: "Waiman pinging for status, asking if patch is merge-able"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Waiting for maintainer response"]
  next_action: "Need maintainer review/ack"
contribution_opportunities: []
generated_at: "2026-07-31T00:10:00"
source_email_count: 1
related_articles: []
tags: [topology]
---
