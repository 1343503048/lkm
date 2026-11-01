# sched/eevdf: Move to a single runqueue

## TL;DR

Chengfeng Lin 的 v3 系列尝试把 EEVDF 从 per-CPU runqueue 收敛到单一 runqueue。本窗口内作者回帖 Mike Galbraith，讨论单 runqueue 下 DELAY_DEQUEUE 的记账行为变化，并给出基准数据：跳过 `__dequeue_task()` 里一次冗余 `update_curr_eevdf()` 在 15-worker 场景基本持平（-0.22%）、2-worker 控制组 +1.27%。方向性重构，合入为时尚早。

## 背景与问题

单一 runqueue 是 EEVDF 方向的重构性探索，目标是消除多核间 per-CPU runqueue 的负载分布与迁移开销。评审关注点之一是对 `DELAY_DEQUEUE` 记账行为的影响：作者此前的测量报告显示单 runqueue 下 requeue 频率发生了变化，Mike Galbraith 指出这可能来自 accounting 改变 DELAY_DEQUEUE 的行为。

## 技术方案

本窗口讨论聚焦于一次微优化：`__dequeue_task()` 开头的 `update_curr_eevdf()` 在 `pick_task_fair()` 已经更新过当前 entity、且其间 selection 未改变 current/rq clock 时是冗余的。作者通过 `pick_next_entity()` 传递一个 already-updated 标志来跳过它；普通 dequeue 与 wakeup-preemption 仍执行更新，lag/eligibility/hierarchy 记账不变。作者也提到曾尝试跳过 v7.3（`c03c1a14507d`）上的一次冗余更新，但未改善 15-worker 场景。

## 版本演进与当前进展

v3（当前，7 补丁系列，本次窗口外发出，cover msgid 未获取到）。v1/v2 不在本次分析窗口内。本窗口内为作者对 Mike 记账质疑的实测回应。

## Maintainer 意见与讨论焦点

Mike Galbraith 提出 accounting 改变 DELAY_DEQUEUE 行为的质疑；作者用数据回应，并询问「这是否是你指的路径，还是另一处 update」，表示愿意再测候选改动。无 NAK、无明确反对，处于技术细节对齐阶段。本窗口内未获取到 Peter Zijlstra / Vincent Guittot / Ingo Molnar 等维护者表态。

## 合入评估

可能性低（low）。单一 runqueue 是调度器核心结构重构，且 DELAY_DEQUEUE 记账影响等关键问题仍在对齐中，尚无维护者认可。阻塞项：需证明单 runqueue 在广泛负载下无回退并消除记账/延迟语义分歧。

## 效果评估

作者数据（原生 CORE 亲和、15s 预热后窗口，每个 worker 数 9 次测量）：15-worker 吞吐 9.171 → 9.158 → 9.186 百万 handoffs/s（baseline → modified → baseline），相对两 baseline 均值 -0.22%；2-worker 控制组 +1.27%。该 pick 路径上的前导 update 很罕见（15 workers 下约每百万 handoffs 1.4 次）。

## 我可以参与的点

- testing：在不同硬件/负载（NUMA、SMT、不同 worker 数）上复现单 runqueue 的 handoff 吞吐与延迟，验证无回退。
- review：评估 DELAY_DEQUEUE 记账在单 runqueue 下的语义变化是否可接受。

## 参考链接

- lore thread: https://lore.kernel.org/all/CANGjgd=DvO72NiB8SC3hNEadmxgzy1niN-mnWyY-LGMJ4H=J0g@mail.gmail.com/
- 系列 cover msgid: 未获取到（本次窗口外）

---
id: sched-20261101-008
subject: "sched/eevdf: Move to a single runqueue"
date: 2026-11-01
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<CANGjgd=DvO72NiB8SC3hNEadmxgzy1niN-mnWyY-LGMJ4H=J0g@mail.gmail.com>"
lore_url: "https://lore.kernel.org/all/CANGjgd=DvO72NiB8SC3hNEadmxgzy1niN-mnWyY-LGMJ4H=J0g@mail.gmail.com/"
authors: [Chengfeng Lin]
maintainers_involved: [Mike Galbraith]
current_version: v3
patch_series:
  - version: v1
    msgid: null
    date: 2026-10-20
    summary: "早期版本，不在本次分析窗口内"
    review_outcome: "未获取到"
  - version: v2
    msgid: null
    date: 2026-10-25
    summary: "早期版本，不在本次分析窗口内"
    review_outcome: "未获取到"
  - version: v3
    msgid: null
    date: 2026-11-01
    summary: "7 补丁系列；本窗口内回帖 Mike Galbraith 讨论 DELAY_DEQUEUE 记账与冗余 update_curr_eevdf() 微优化"
    review_outcome: "Mike 提出 accounting 质疑，作者以基准数据回应，细节对齐中"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "单一 runqueue 为调度核心结构重构，DELAY_DEQUEUE 记账影响等关键问题仍在对齐"
  next_action: "需证明单 runqueue 在广泛负载下无回退，并消除记账/延迟语义分歧"
contribution_opportunities:
  - kind: testing
    description: "在不同硬件/负载上复现单 runqueue 的 handoff 吞吐与延迟"
  - kind: review
    description: "评估 DELAY_DEQUEUE 记账在单 runqueue 下的语义变化"
generated_at: "2026-11-02T09:00:00"
source_email_count: 1
related_articles: []
tags: [eevdf, cfs]
---