# sched/core: Call wq_worker_tick() for the execution context

## TL;DR

Hui Su 指出 proxy execution 下 `wq_worker_tick()` 取错上下文：`rq->donor` 是调度上下文、
`rq->curr` 才是执行上下文，导致 worker 的 CPU 时间记账与 CPU-intensive 判定失真。9/2 23:02 发出，
workqueue 维护者 Tejun Heo 9/3 02:21 已回。

## 背景与问题

工作队列（workqueue）worker 的节流/记账依赖 `wq_worker_tick()` 在合适时机被调用。
本期（UID 74505）提出在「执行上下文（execution context）」路径上也调用
`wq_worker_tick()`，使 worker 的 tick 记账在更多执行场景下保持一致。

## 技术方案

- `sched/core: Call wq_worker_tick() for the execution context`：在调度核心的执行上下文
  相关路径补上 `wq_worker_tick()` 调用。

## 版本演进与当前进展

- 当前状态：**under_review**（新补丁）。
- 合入可能性 medium；影响 workqueue 节流记账准确性，需确认无副作用。

## Maintainer 意见与讨论焦点

- 作者的问题陈述（74394）："wq_worker_tick() accounts CPU time and detects CPU-intensive work for
  the kworker that is actually running. With proxy execution, rq->donor is the scheduling context while
  rq->curr is the execution co…"（截断）。
- 唯一回帖来自正确的维护者 Tejun Heo（74950，9/3 02:21），但缓存只保留引文头，看不到他是否认可、是否要求
  改动——**结论性意见缺失**。调度侧（Peter Zijlstra / John Stultz）当天没有介入。
- 无 NAK。这是 001 那批 PE 合入后连续第 2 个「上下文语义外溢」修复；另一个 `fix task_sched_runtime()`
  （73775，同日 19:25）至今零回帖。

## 合入评估

**中**。补丁小、指向明确、维护者已在一天内接手，但 (1) Tejun 的意见正文缺失，无法判断是否需 v2；
(2) 这类修正该走 workqueue 树还是 sched 树没定，容易和 73775、74668 抢同一批上下文语义定义。

## 效果评估

暂无效果数据。无人报告过因 worker 记账失真导致的实际症状（如 worker 被误判为 CPU-intensive 而被
resched/迁移），只是代码路径推论，属作者判断。

## 我可以参与的点

- 直接回 74950 这条线：开 PROXY_EXEC 跑 unbound workqueue + 长时间 CPU 密集 worker，观察 worker 的
  CPU 归属与 rescuer 行为是否变化，给 Tejun 一个实测结论。
- 把 73775 / 74394 / 74668 三封同类补丁合起来提一个「PE 下统一取执行上下文」的整理建议——现在是一个补丁
  一个补丁地补，且 73775 完全没人理。

## 参考链接

- 002 sched/core 清理（同属调度核心活跃改动）

---
id: sched-20260902-012
date: '2026-09-02'
subject: 'sched/core: Call wq_worker_tick() for the execution context'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Hui Su
- Tejun Heo
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - "Tejun Heo 的回帖正文缺失，无法判断是否需要 v2"
  - "同类修正（73775/74394/74668）分散且未确定合入路径（sched 树还是 workqueue 树）"
  - "无线上症状或实测数据支撑"
  next_action: "在 PROXY_EXEC 下实测 worker 记账并回 74950，同时把三封同类修正合并讨论"
contribution_opportunities:
- "开 PROXY_EXEC 跑 CPU 密集的 unbound workqueue，验证 wq_worker_tick() 的执行上下文归属并回帖"
- "把 task_sched_runtime() / wq_worker_tick() / task_tick_cache() 三处 execution-context 修正合并成一个整理方案"
- "接手当天零回帖的 sched/core: fix task_sched_runtime() for proxy execution（73775）"
source_email_count: 2
related_articles: []
tags:
- sched/core
---
