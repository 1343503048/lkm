# sched/fair: Fix flat hierarchy

## TL;DR
Vincent Guittot 修复 sched/fair 在 flat hierarchy 下 delayed-dequeue 实体的 `update_curr` 缺失问题。Peter 测试后已推到 `sched/urgent`，并把 7.2 的 `requeue_delayed_entity()` 适配改动推到 `sched/core`。已合入 tip 队列（merged_tip）。

## 背景与问题
在 flat hierarchy（系统未使用任务组/cgroup）场景下，delayed-dequeue 实体（被延迟出队的 task）在主路径 `requeue_delayed_entity()` 与 `reweight_eevdf()`（非 curr 情形）处需要 `update_curr` 来刷新 vruntime/lag，但原代码未在该路径调用，导致 lag 统计与权重重算基于陈旧值，影响 EEVDF 的公平性与延迟。

## 技术方案
在 `requeue_delayed_entity()` 开头补 `update_curr(cfs_rq)`，使 delayed 实体在被重新入队前先刷新当前运行统计；并对 `reweight_eevdf()` 的非 curr 情形保持一致。Peter 同时在 7.2 适配：把该 `update_curr` 加入 `requeue_delayed_entity()`，并区分 urgent（含此修复）与 core（讨论中的更大改动）。

## 版本演进与当前进展
当前 v1。邮件链（40429 等 5 封）显示 Vincent 与 Peter 经多轮确认，Peter 已 push 到 sched/urgent 与 sched/core（queue.git），待推 tip。

## Maintainer 意见与讨论焦点
焦点是把最小修复放 sched/urgent、更完整改动放 sched/core 的拆分是否恰当。Peter 接受该拆分并催促 Vincent 复核。

## 合入评估
已合入 tip 队列（merged_tip）。无阻塞项，下一步进主线/稳定分支。

## 效果评估
无独立 benchmark；修复 EEVDF lag/weight 统计正确性，正向公平性收益。

## 我可以参与的点
- 在 flat hierarchy 配置下做延迟/公平性回归验证；
- 跟踪 unstable/stable 分支的 backport。

## 参考链接
- tip 分支: tip/sched/urgent, tip/sched/core
- 关联: EEVDF delayed-dequeue

---
subject: "sched/fair: Fix flat hierarchy"
id: sched-20260814-001
date: 2026-08-14
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20260814132200.fair-flat-hierarchy@vg>"
lore_url: "未获取到"
authors: [Vincent Guittot]
maintainers_involved: [Peter Zijlstra, Ingo Molnar, Dietmar Eggemann, Juri Lelli]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260814132200.fair-flat-hierarchy@vg>"
    date: 2026-08-14
    summary: "修复 sched/fair 在 flat hierarchy（无任务组）场景下 delayed-dequeue 实体的 update_curr 调用缺失，导致 requeue_delayed_entity/ reweight_eevdf 时 lag 统计不一致。"
    review_outcome: "Peter 测试后将修复推到 sched/urgent，并把 7.2 的 requeue_delayed_entity() 适配改动推到 sched/core（queue.git）。"
upstream_commit: "未获取到完整 hash（已推 sched/urgent 与 sched/core）"
fixes_commit: null
merged_branch: "tip/sched/urgent + tip/sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "已进入 tip 队列（urgent + core），等待后续进入主线与稳定分支。"
contribution_opportunities:
  - kind: testing
    description: "在 flat hierarchy（无 cgroup 任务组）配置下验证 delayed-dequeue 实体的 lag/weight 统计正确。"
generated_at: "2026-08-15T00:15:00"
source_email_count: 5
related_articles: []
tags: [sched/fair, eevdf]
---
