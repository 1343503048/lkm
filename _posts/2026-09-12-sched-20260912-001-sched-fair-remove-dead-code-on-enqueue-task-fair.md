---
id: sched-20260912-001
subject: 'sched/fair: remove dead code on enqueue_task_fair()'
date: '2026-09-12'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved: []
current_version: v3
patch_series:
- version: v1 (无版本号投递)
  msgid: <20260911155449.1249726-1-kayracizmeci@gmail.com>
  date: 2026-09-11
  summary: 删除 enqueue_task_fair() 不可达的 cfs_rq->curr == se 分支（-13/+3）。
  review_outcome: 无回帖；PeterZ 此前在 place_entity 线程给出等价 diff。
- version: v3
  msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
  date: 2026-09-12
  summary: 补上版本号重发（作者自述漏标 v3），diff 与前次投递逐行一致。
  review_outcome: 当日无回帖。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 独立补丁与 place_entity 系列 v3 的归属未定，存在重复推进风险
  next_action: 等维护者择一收取；若 v3 吸收本清理则标记本补丁 superseded
contribution_opportunities:
- kind: testing
  description: core-sched 等配置下长跑 WARN_ON_ONCE 验证不可达
- kind: review
  description: 跟进 place_entity v3 与本补丁的归并结果
generated_at: '2026-09-14T12:40:00'
source_email_count: 1
related_articles:
- sched-20260911-020
- sched-20260911-015
tags:
- cfs
title: 'sched/fair: remove dead code on enqueue_task_fair()'
layout: article
---

## TL;DR
Kayra Cizmeci 补发带版本号的 v3：删除 enqueue_task_fair() 中不可达的 `cfs_rq->curr == se` 分支（-13/+3），diff 与 09-11 的无版本号投递逐行一致——作者自述「忘了标 v3」。这是 place_entity 系列（PeterZ 判定 curr==se 不可达）与独立清理补丁两条线索的正式归并版本，当日仍无回帖。本文为增量更新，前情见 sched-20260911-020、sched-20260911-015。

## 背景与问题
enqueue_task_fair() 中 `curr = (cfs_rq->curr == se)` 为真时走 place_entity(cfs_rq, se, flags) 独立分支、跳过常规入队路径。该前提在 09-11 的 place_entity 系列讨论中被 Peter Zijlstra 论证为不可达（enqueue 时 se 不可能是 cfs_rq->curr），作者当天以 WARN_ON_ONCE 测试佐证并承诺发 v3；本补丁即该方向的独立实现。

## 技术方案
- 删除 `bool curr` 变量、`curr = (cfs_rq->curr == se)` 判定与 `if (curr) place_entity(...)` 调用；
- 解除 `if (!curr) {...}` 包裹，reweight_eevdf() / place_entity(ENQUEUE_QUEUED) / __enqueue_entity() 成为无条件顺序执行；
- 顺带删除遗留的 `/* XXX comment on the curr thing */` 注释；requeue_delayed_entity() 与 dl_server_start() 逻辑不动。

## 版本演进与当前进展
*current_version: v3（msgid `<20260911160253.1249960-1-kayracizmeci@gmail.com>`，09-12 00:02 入缓存）*。

- 09-11 23:54：以无版本号的 `[PATCH]` 投递（见 sched-20260911-020）；
- 09-12 00:02：补发 `[PATCH v3]`，cover 注明「Ah.. I forgot to add v3. Sorry of the other one.」——diff 与前次投递完全一致（同一 blob 对 440e4fdebe2f），本次只是把版本号补上；
- 当日无回帖。place_entity 系列（sched-20260911-015）承诺的 v3 当日缓存内未出现，两条线索的最终归并形态仍待观察。

## Maintainer 意见与讨论焦点
本补丁自身当日无新回帖；既有的支持性意见来自 PeterZ（09-11 在 place_entity 线程给出等价 diff）。无反对意见记录；潜在关注点仍是删除后 enqueue 路径确无 curr == se 的隐藏入口。

## 合入评估
*likelihood=medium*：方向有 PeterZ 的 diff 背书、版本号已补齐；但维护者尚未对独立补丁表态，且 place_entity 系列 v3 仍未发出——存在同一清理双线推进的重复风险。*blocking_issues*：独立补丁与 place_entity 系列 v3 的归属未定。*next_action*：等维护者择一收取；若 place_entity v3 出现并包含本清理，本补丁应标记 superseded。

## 效果评估
无性能数据；效果为热路径去分支与可读性清理，作者此前自评性能影响不可测量。

## 我可以参与的点
- kind=testing：core-sched/异常 enqueue 配置下长跑 WARN_ON_ONCE(cfs_rq->curr == se)，为「不可达」提供作者之外的证据（承 09-11 的验证点）。
- kind=review：跟进 place_entity 系列 v3 发出后与本补丁的归并结果，避免主线收到重复/冲突清理。

## 参考链接
- v3 补丁：https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
- 09-11 的初次投递：https://lore.kernel.org/all/20260911155449.1249726-1-kayracizmeci@gmail.com/
- PeterZ 的等价 diff（place_entity 线程）：https://lore.kernel.org/all/20260911124256.GZ776954@noisy.programming.kicks-ass.net/
