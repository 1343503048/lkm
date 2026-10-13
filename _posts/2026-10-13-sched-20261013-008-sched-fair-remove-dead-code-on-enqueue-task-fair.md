---
id: sched-20261013-008
subject: 'sched/fair: remove dead code on enqueue_task_fair()'
date: 2026-10-13
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
current_version: v3
patch_series:
- version: v3
  msgid: <20260911160253.1249960-1-kayracizmeci@gmail.com>
  date: 2026-09-11
  summary: 删除 enqueue_task_fair() 里不可达的 cfs_rq->curr == se 分支
  review_outcome: 已合入 tip/sched/core (819224e506bc)，但引入 CFS_BANDWIDTH 回归，Peter 给修复
    diff
upstream_commit: 819224e506bc
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 正式修复补丁待落，Christian 的 lag 双计疑问待确认
  next_action: 落正式修复补丁（cfs_rq->curr != se 保护），Peter 复审收取
contribution_opportunities:
- kind: testing
  description: 在 CFS_BANDWIDTH 场景复现并验证修复是否消除 WARNING
- kind: review
  description: 核查 Christian 提出的 place_entity lag 双计疑问是否仍成立
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261012-010
tags:
- cfs
- regression
title: 'sched/fair: remove dead code on enqueue_task_fair()'
layout: article
---

> **subject**：sched/fair: remove dead code on enqueue_task_fair()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-020-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20260911-020</a> / 20260912-001：Kayra Cizmeci 发「remove dead code on enqueue_task_fair()」清理补丁（删不可达的 `cfs_rq->curr == se` 分支），后与 Peter 的 place_entity 系列合流。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-010-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20261012-010</a>：该补丁已合入 tip/sched/core（819224e506bc），但 Christian Loehle 发现其引入回归——CFS_BANDWIDTH 下任务 throttle→dequeue→unthrottle→enqueue 命中 `cfs_rq->curr == se` 触发 WARNING；Peter 给出 `if (cfs_rq->curr != se) __enqueue_entity()` 的修复 diff。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-008-sched-fair-remove-dead-code-on-enqueue-task-fair.html">sched-20261013-008</a>（今天）：Peter 回应 Christian 提出的 place_entity 双计 lag 疑问——修复后仍只有一处 `place_entity()`（位于 `enqueue_hierarchy()` 之后、带 `ENQUEUE_QUEUED`），`ENQUEUE_QUEUED` 正是告诉 place_entity「entity 已计入 h_nr_queued」从而正确调整；Kayra 追问 Christian 是否指的是 `se == curr && on_rq == 1` 下的 lag 双计。

## 背景与问题
（承接 20260911/20260912/20261012-010）原「dead code」补丁删除了 `enqueue_task_fair()` 里被认为不可达的 `cfs_rq->curr == se` 分支；但 CFS_BANDWIDTH 场景任务可被 throttle 后、schedule out 前又被 wakeup——此时 `cfs_rq->curr` 仍是它、`on_rq` 却为 false，unthrottle 路径重新 enqueue 该 curr 会命中被删分支而触发 WARNING。Peter 的修复方向是把无条件 `__enqueue_entity()` 改为 `if (cfs_rq->curr != se)`。今天讨论继续深挖另一层：Christian 担忧 dequeue→enqueue 会把（dequeue 时保存的）lag 二次计入——dequeue 后 `curr==se, on_rq==0` 被排除平均，enqueue_hierarchy 又因 `curr==se, on_rq==1` 计入，place_entity 却按「se 被排除」的假设计算放置。

## 技术方案
（承接 20261012-010）Peter 的修复：`if (cfs_rq->curr != se) __enqueue_entity(cfs_rq, se);` 并加注释说明 CFS_BANDWIDTH 下的 throttle/dequeue→unthrottle/wakeup 时序。今天 Peter 进一步澄清 double-account 的疑问：修复后代码里 `place_entity()` 仍只有一处、位于 `enqueue_hierarchy()` 之后且带 `ENQUEUE_QUEUED` 标志；`enqueue_hierarchy()` 把 entity 计入 `h_nr_queued`，而 `ENQUEUE_QUEUED` 正是向 `place_entity()` 表明这一点、使其能据此调整——故不构成双计。Kayra 则向 Christian 确认担忧点是否为「`se == curr && on_rq == 1` 时 lag 被双重记账」。

## 版本演进与当前进展
当前 v3（已合入 tip/sched/core 的 819224e506bc 即该清理补丁；回归讨论围绕是否 revert 或补保护）。今日为回归讨论的延续，无新版本补丁；Peter 已给修复 diff，正式补丁待落。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：认为 double-account 担忧不成立，解释 place_entity + ENQUEUE_QUEUED 的语义，坚持 `if (cfs_rq->curr != se)` 的修复思路。
- **Christian Loehle**：定位回归、给出 Tested-by，并提出 place_entity 双计 lag 的更深疑问。
- **Kayra Cizmeci**：承接 Peter 与 Christian，试图澄清 Christian 的 lag 双计具体指何时何分支。
- 焦点已从「是否回归」推进到「修复 diff 是否完备、lag 是否双计」这一细节收尾。

## 合入评估
*likelihood=high*。回归明确、有 splat、Peter 已给修复方向与解释、Christian Tested-by。*blocking_issues*：正式修复补丁待发出；Christian 的 lag 双计疑问待确认是否仍成立。*next_action*：Kayra（或 Christian）落正式修复补丁（`if (cfs_rq->curr != se)` + 注释），Peter 复审收取。

## 效果评估
无新增性能数据；触发的 WARNING（`enqueue_task_fair+0x7a8`）来自 CFS_BANDWIDTH 回归（arm64 PREEMPT_RT），修复以消除 WARNING 与正确性为主。

## 我可以参与的点
- review/testing：可对照 Peter 的 diff 在 CFS_BANDWIDTH 场景复现/验证 WARNING 是否消除，并核查 Christian 提出的 lag 双计疑问是否仍成立。
- discussion：该回归与「sched/eevdf: Fix vprot across reweighting」系列（<a class="article-ref" href="/lkm/2026/10/13/sched-20261013-017-sched-eevdf-fix-vprot-across-reweighting.html">sched-20261013-017</a>）在 `reweight_eevdf()`/`cfs_rq->curr` 上相互牵连，可一并关注。

## 参考链接
- 系列补丁 lore（20260912）：https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
- 今日 Peter 回帖：https://lore.kernel.org/all/20261013115835.GI2009045@noisy.programming.kicks-ass.net/
