---
id: sched-20261012-010
date: '2026-10-12'
subject: 'sched/fair: remove dead code on enqueue_task_fair()'
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- Peter Zijlstra
- Christian Loehle
current_version: v3
patch_series:
- version: v3
  msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
  date: '2026-09-11'
  summary: 删除 enqueue_task_fair() 中不可达的 cfs_rq->curr == se 分支
  review_outcome: 已合入 tip/sched/core（819224e506bc），10-12 发现 CFS_BANDWIDTH 下回归，Peter
    提修复 diff
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 的修复 diff 需落成正式补丁
  - Christian 指出 dequeue->enqueue 让 place_entity 双计 lag 的问题待确认
  next_action: Kayra 把 Peter 的「cfs_rq->curr != se 才 __enqueue_entity」落成正式补丁，Christian
    复核 double-account 后交 Peter 收取或 revert 819224e506bc
contribution_opportunities:
- kind: testing
  description: 在 CFS_BANDWIDTH（cpu.max 写）下复现 enqueue_task_fair 的 WARNING，验证 Peter
    的修复 diff
- kind: review
  description: 分析 dequeue()->enqueue() 时 place_entity 是否会对保存的 lag 双计（Christian 提出的问题）
generated_at: '2026-10-13T01:40:00'
source_email_count: 5
related_articles:
- sched-20260911-020
- sched-20260912-001
- sched-20260925-003
tags:
- cfs
- regression
title: 'sched/fair: remove dead code on enqueue_task_fair()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-020-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20260911-020</a> / 20260912-001：Kayra 发「remove dead code on enqueue_task_fair()」清理补丁（删不可达的 `cfs_rq->curr == se` 分支），两线索与 PeterZ 的 place_entity 系列判断合流。
- <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-003-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20260925-003</a>：该补丁已被 Peter Zijlstra 合入 tip/sched/core（commit 819224e506bc）。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-010-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20261012-010</a>（今天）：Christian Loehle 发现该 commit 引入回归——CFS_BANDWIDTH 下任务 throttle→dequeue→（未 schedule out 前）unthrottle→enqueue 会命中 `cfs_rq->curr == se`，触发 `enqueue_task_fair` 的 WARNING；Peter 给出「`if (cfs_rq->curr != se) __enqueue_entity()`」的修复 diff，Christian 已对 reproducer 给 `Tested-by` 并追问 place_entity 双计 lag 的问题。

## 背景与问题

（承接 20260911/20260912/20260925）原补丁认为 `enqueue_task_fair()` 里 `cfs_rq->curr == se` 不可达而删除分支。但 CFS_BANDWIDTH 场景推翻这一假设：任务被 throttle、在回到用户态真正 dequeue 之前又收到 wakeup——它确实被 dequeued 但从未 schedule out（put_prev_task 未跑），此时 `cfs_rq->curr` 仍是它、`on_rq` 却为 false。unthrottle 路径（`tg_unthrottle_up→unthrottle_cfs_rq→tg_set_bandwidth→cpu_max_write`）会重新 enqueue 这个 curr，命中被删的分支，触发 WARNING（Christian 贴出 arm64 PREEMPT_RT 上的 splat，`enqueue_task_fair+0x7a8`）。Christian 认为需要在 tip/sched/core revert 819224e506bc 或补回保护。

## 技术方案

Peter 判断「此场景与最初的 use-case 不同——当初是遍历 cgroup 层级时 dequeue/re-enqueue，须表现得中间什么都没发生；这次允许推进时间」。他给出 diff：把无条件 `__enqueue_entity(cfs_rq, se)` 改为 `if (cfs_rq->curr != se) __enqueue_entity(cfs_rq, se);`，并加注释说明 CFS_BANDWIDTH 下任务可在 schedule out 前被 throttle/dequeue 再 unthrottle/woken。Christian 补充：dequeue→enqueue 还会让 `place_entity()` 对（dequeue 时保存的）lag 二次计入——dequeue 后 `curr==se, on_rq==0` 被排除平均，enqueue_hierarchy 又 `curr==se, on_rq==1` 计入，place_entity 却按「se 被排除」的假设计算放置。

## 版本演进与当前进展

- v3（09-11）→ 合入 tip/sched/core（09-25，819224e506bc）。
- 10-12：Christian 报回归（贴 splat）、Peter 给修复 diff、Christian 对 reproducer `Tested-by`（"Tested-by: Christian Loehle"）+ 提 double-account 疑问；Kayra 表示「需要修，会测试」。
- 尚无正式 revert 或修复补丁落出。

## Maintainer 意见与讨论焦点

- **Christian Loehle**：定位到 unthrottle 路径的 WARNING，主张 revert 819224e506bc 或补保护；给出 `Tested-by`，同时提出 place_entity 双计 lag 的深层疑问。
- **Peter Zijlstra**：认为是 CFS_BANDWIDTH 特有（任务 throttle 后、schedule out 前被 wakeup），给出一行修复 diff + 注释，并指出正常 block/wakeup 路径也「差点」命中（balance 掉 rq->lock 后 dequeue），只是 ttwu 有 `->on_cpu` 挡着而 unthrottle 路径没有。

## 合入评估

*likelihood=high*。回归明确、有 splat、Peter 已给修复方向、Christian `Tested-by`。*blocking_issues*：修复 diff 待落正式补丁、double-account 问题待澄清。*next_action*：Kayra 落正式修复补丁（或先 revert 819224e506bc），Christian 复核 double-account 后交 Peter。

## 效果评估

Christian 提供 arm64 PREEMPT_RT 上的 WARNING splat（Radxa Orion O6，7.3.0-rc1，`enqueue_task_fair+0x7a8`，调用链 `tg_unthrottle_up→...→cpu_max_write`）；无性能数字（正确性/告警类回归）。

## 我可以参与的点

- `testing`：用 `cpu.max`（cgroup 带宽）反复写触发 throttle/unthrottle，复现 WARNING 并验证 Peter 的 `cfs_rq->curr != se` 修复。
- `review`：分析 dequeue→enqueue 时 `place_entity()` 是否对保存 lag 双计（Christian 抛出的问题），决定是否需要一并修。

## 参考链接

- lore（Christian 报回归 + splat）: https://lore.kernel.org/all/fd3f9d83-cb5b-496b-b7c1-b40f31cf795e@arm.com/
- lore（Peter 修复 diff）: https://lore.kernel.org/all/20261012140225.GU2009045@noisy.programming.kicks-ass.net/
- lore（Christian Tested-by + double-account 疑问）: https://lore.kernel.org/all/5661a8d7-1a83-4336-b238-589f598075cf@arm.com/
