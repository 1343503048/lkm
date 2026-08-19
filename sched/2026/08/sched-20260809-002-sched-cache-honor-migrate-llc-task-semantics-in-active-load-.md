# sched cache honor migrate llc task semantics in active load 

## TL;DR
Lu Wang 提交 v2，让 active load balance 尊重 `migrate_llc_task` 的缓存感知迁移语义，避免把被标记 prefer-LLC 的任务不必要地跨 LLC 搬移。处于 under_review。

## 背景与问题
`migrate_llc_task` 用于标记希望留在同一 LLC 内的任务（缓存局部性优化）。但在 active load balance（当前 CPU 过载、需要主动把任务搬到空闲 CPU）路径中，原有逻辑未考虑该标记，可能把一个 prefer-LLC 任务搬到另一个 LLC，反而损害缓存命中。

## 技术方案
在 active load balance 的候选选择/触发判断中纳入 `migrate_llc_task` 语义：若任务被标记 prefer-LLC，则优先在同 LLC 内寻找目标，而非直接跨 LLC 迁移。设计取舍是「缓存局部性优先于瞬时均衡」——仅在同 LLC 无空闲容量时才放宽到跨 LLC。

## 版本演进与当前进展
当前 v2。v1 首次提出该思路；v2 完善语义并调优判断条件。v2 于 8/8 发出，暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者明确意见。预期讨论点：active load balance 增加判断是否会加大均衡延迟，以及在极端拓扑下是否会出现「找不到同 LLC 目标而停滞」的边界。

## 合入评估
合入可能性 medium。方向合理，但需 bench 数据证明缓存命中提升大于均衡延迟代价。

## 效果评估
暂无效果数据（邮件未附 benchmark）。

## 我可以参与的点
- 在 NUMA/多-LLC 拓扑上跑 hackbench/stream 等对比缓存命中与均衡频率；
- 评审 active load balance 路径的边界条件正确性。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到

---
subject: "sched cache honor migrate llc task semantics in active load "
id: sched-20260809-002
date: 2026-08-09
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: "<20260808.cache.v2@wanglu>"
lore_url: "未获取到"
authors: [Lu Wang]
maintainers_involved: [Peter Zijlstra, Vincent Guittot, Dietmar Eggemann]
current_version: v2
patch_series:
  - version: v1
    msgid: "<unknown-v1>"
    date: 2026-08-02
    summary: "首次提出在 active load balance 路径中考虑 migrate_llc_task 语义。"
    review_outcome: "暂未收集到 v1 的具体 review 意见。"
  - version: v2
    msgid: "<20260808.cache.v2@wanglu>"
    date: 2026-08-08
    summary: "v2 把 migrate_llc_task 缓存感知的迁移语义纳入 active load balance 的触发判断，避免跨 LLC 不必要地搬移被标记为 prefer-LLC 的任务。"
    review_outcome: "v2 刚发出，暂无维护者明确 ack/nak。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "需要维护者确认 active load balance 路径引入该判断不会增加均衡延迟，最好有 bench 数据。"
contribution_opportunities:
  - kind: review
    description: "评审 active load balance 路径新增判断的代价与正确性。"
  - kind: testing
    description: "在 NUMA/多 LLC 拓扑机器上对比开启前后的负载均衡频率与缓存命中率。"
generated_at: "2026-08-10T00:15:00"
source_email_count: 1
related_articles: []
tags: [sched/cache, sched/fair]
---
