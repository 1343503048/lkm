# sched/fair: Prefer waker CPU for non-SMT reciprocal sync wakeups

## TL;DR

Shubhang 的 v3 补丁优化同步唤醒的 CPU 选择：对于非 SMT 系统的 reciprocal sync wakeup，优先选择 waker CPU 以保持 cache 热度。K Prateek Nayak 提供了将 SMT 检查推入 `select_idle_sibling()` 的代码建议，等待作者整合。

## 背景与问题

同步唤醒（sync wakeup）场景中，唤醒者和被唤醒任务之间存在数据依赖。当前 `select_idle_sibling()` 可能选择非 waker CPU，导致 cache 冷启动。对于非 SMT 系统的 reciprocal sync wakeup（两个任务互相唤醒），优先选择 waker CPU 可以利用 cache 热度。

## 技术方案

v3 方案：
- 非 SMT 系统：直接选择 waker CPU
- SMT 系统：保持原有行为（fallback 到 select_idle_sibling）

K Prateek 建议将 SMT 检查进一步推入 `select_idle_sibling()` 内部，在已知 `test_idle_core()` 返回值时再做决策，而不是在调用前判断。他提供了具体的代码 diff：
- 修改 `select_idle_smt()` 参数从 `sched_domain *sd` 改为 `root_domain *rd`
- 在 `select_idle_sibling()` 内部整合 SMT 检查逻辑

## 版本演进与当前进展

- v1 (2026-07-22): 初始提案
- v2 (2026-07-25): 回应 review 意见
- v3 (2026-07-27): 限定为非 SMT reciprocal sync wakeups
- 2026-07-30: K Prateek 提供 SMT 整合代码建议

## Maintainer 意见与讨论焦点

- K Prateek Nayak: 提供了具体的代码整合建议，方向认可
- Christian Loehle: v2 时建议改进 SMT 处理

## 合入评估

- **likelihood**: medium
- 方向被认可，但需要整合 SMT 处理
- 可能需要 benchmark 数据证明收益

## 效果评估

暂无具体性能数据。

## 我可以参与的点

- **实现 SMT 整合**：可以基于 K Prateek 的代码建议实现 v4，将 SMT 检查推入 `select_idle_sibling()`
- **测试验证**：在 SMT 和非 SMT 系统上测试 wakeup placement 效果

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260727-b4-sched-sync-wakeup-v3-1-90cf
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
subject: "sched/fair: Prefer waker CPU for non-SMT reciprocal sync wakeups"
id: sched-20260730-004
date: 2026-07-30
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20260727-b4-sched-sync-wakeup-v3-1-90cf...@amd.com>"
lore_url: "https://lore.kernel.org/lkml/20260727-b4-sched-sync-wakeup-v3-1-90cf"
authors: [Shubhang]
maintainers_involved: [K Prateek Nayak, Christian Loehle]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20260722-b4-sched-sync-wakeup-v1-1-f116...>"
    date: 2026-07-22
    summary: "Initial proposal to prefer waker CPU for reciprocal sync wakeups"
    review_outcome: "Christian suggested improvements for SMT systems"
  - version: v2
    msgid: "<20260722-b4-sched-sync-wakeup-v2-1-f116...>"
    date: 2026-07-25
    summary: "Addressed some review feedback"
    review_outcome: "K Prateek suggested pushing SMT check into select_idle_sibling()"
  - version: v3
    msgid: "<20260727-b4-sched-sync-wakeup-v3-1-90cf...>"
    date: 2026-07-27
    summary: "Prefer waker CPU for non-SMT reciprocal sync wakeups, with SMT fallback"
    review_outcome: "K Prateek provided code suggestion for SMT integration"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["Need to integrate K Prateek's SMT suggestion", "May need benchmark data"]
  next_action: "Incorporate select_idle_sibling() integration for SMT systems"
contribution_opportunities:
  - kind: testing
    description: "Test on SMT and non-SMT systems to validate wakeup placement"
  - kind: extend
    description: "Implement K Prateek's suggestion to push SMT check into select_idle_sibling()"
generated_at: "2026-07-31T00:10:00"
source_email_count: 2
related_articles: []
tags: [cfs, affinity, perf]
---
