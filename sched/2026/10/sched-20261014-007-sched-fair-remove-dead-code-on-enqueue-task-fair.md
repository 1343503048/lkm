# sched/fair: remove dead code on enqueue_task_fair()

> **subject**：sched/fair: remove dead code on enqueue_task_fair()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261012-010：Kayra 的「remove dead code on enqueue_task_fair()」已合入 tip/sched/core（819224e506bc），但引入 CFS_BANDWIDTH 回归（throttle→dequeue→unthrottle→enqueue 命中被删分支触发 WARNING）；Peter 给出 `if (cfs_rq->curr != se) __enqueue_entity()` 修复 diff。
- sched-20261013-008：Peter 解释修复后仍只有一处 `place_entity()`（`enqueue_hierarchy()` 之后、带 `ENQUEUE_QUEUED`），`ENQUEUE_QUEUED` 正是告知 place_entity「entity 已计入 h_nr_queued」，不构成 lag 双计；Kayra 追问 Christian 的担忧点是否为 `se == curr && on_rq == 1`。
- sched-20261014-007（今天）：Christian Loehle 回「Exactly」确认了 Peter 的解释，但进一步指出 **`place_entity()` 里 `avg_vruntime_weight(cfs_rq, se->h_load.weight)` 仍假定 `se` 尚未计入 cfs_rq 权重——在 enqueue→dequeue（unthrottle）场景里它其实还在**，即该假设在具体时序下仍不成立。

## 背景与问题
（承接 20261012-010/20261013-008）原「dead code」补丁删除了 `enqueue_task_fair()` 里被认为不可达的 `cfs_rq->curr == se` 分支；CFS_BANDWIDTH 下任务 throttle 后、schedule out 前又被 wakeup，`cfs_rq->curr` 仍是它而 `on_rq` 为 false，unthrottle 重新 enqueue 该 curr 命中被删分支触发 WARNING。今天讨论继续收尾另一层：dequeue→enqueue 时 `place_entity()` 的权重参数假设是否成立。

## 技术方案
（承接 20261012-010）Peter 的修复：`if (cfs_rq->curr != se) __enqueue_entity(cfs_rq, se);`。今日 Christian 的增量指出：

```c
// place_entity(ENQUEUE_QUEUED) 里仍做：
load = cfs_rq->sum_weight;
if (curr && curr->on_rq)            // <-- enqueue_hierarchy() 之后为真
    load += avg_vruntime_weight(cfs_rq, curr->h_load.weight);
weight = avg_vruntime_weight(cfs_rq, se->h_load.weight); // <- 假定 se 尚未计入 cfs_rq 权重，但此刻它（仍）在
lag *= load + weight;
```

即 `place_entity()` 的 `se` 权重项仍按「se 尚未计入 sum_weight」计算，而具体 enqueue→dequeue（unthrottle）时序里 se 仍留在权重里，双计问题是否已彻底解决仍取决于 `ENQUEUE_QUEUED` 如何调整——Christian 把这个细节摆出来待 Peter/Kayra 定论。

## 版本演进与当前进展
当前 v3（已合入 tip/sched/core 的 819224e506bc 即该清理补丁；回归讨论围绕 revert 或补保护）。今日为回归讨论的延续，仍无正式修复补丁落盘；Peter 已给修复 diff，Christian 补一个 place_entity 权重假设的细节。

## Maintainer 意见与讨论焦点
- **Christian Loehle**（今日）：确认 Peter 解释「Exactly」，但补充 place_entity 权重项在 enqueue→dequeue 时序下的假设裂缝。
- **Peter Zijlstra**（前日）：认为双计不成立，坚持 `if (cfs_rq->curr != se)` 修复。
- 焦点已细化为「place_entity 在 `ENQUEUE_QUEUED` + unthrottle 时序下是否仍引入 lag 双计」这一实现级收尾，无 NAK。

## 合入评估
*likelihood=high*。回归明确、有 splat、Peter 已给修复方向，Christian 的 Tested-by 与今日细节都在收敛收尾。*blocking_issues*：正式修复补丁待落；Christian 提出的 place_entity 权重假设裂缝待确认。*next_action*：落正式修复补丁（`if (cfs_rq->curr != se)` + 注释），确认 place_entity 权重项后由 Peter 复审收取。

## 效果评估
无新增性能数据；触发 WARNING（`enqueue_task_fair`）来自 CFS_BANDWIDTH 回归（arm64 PREEMPT_RT），修复以消除 WARNING 与正确性为主。

## 我可以参与的点
- review/testing：对照 Peter 的 diff 在 CFS_BANDWIDTH 场景复现并验证 WARNING 消除，重点核查 Christian 指出的 place_entity `avg_vruntime_weight()` 权重假设在 enqueue→dequeue 时序下的影响。
- discussion：该回归与 vprot 系列（sched-20261014-006）在 `reweight_eevdf()`/`cfs_rq->curr` 上相互牵连，可一并关注。

## 参考链接
- 系列补丁 lore（20260912）：https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/
- 今日 Christian 回帖：https://lore.kernel.org/all/6f7ec108-603a-45c3-a5c2-6f9aebb50f54@arm.com/

---
id: sched-20261014-007
subject: 'sched/fair: remove dead code on enqueue_task_fair()'
date: 2026-10-14
subsystem: sched
type: regression
status: under_review
severity: high
thread_root_msgid: '<20260911160253.1249960-1-kayracizmeci@gmail.com>'
lore_url: 'https://lore.kernel.org/all/20260911160253.1249960-1-kayracizmeci@gmail.com/'
authors:
  - 'Kayra Cizmeci'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v3
patch_series:
  - version: v3
    msgid: '<20260911160253.1249960-1-kayracizmeci@gmail.com>'
    date: 2026-09-11
    summary: '删除 enqueue_task_fair() 里不可达的 cfs_rq->curr == se 分支'
    review_outcome: '已合入 tip/sched/core(819224e506bc)；引入 CFS_BANDWIDTH 回归，Peter 给修复 diff，Christian 补 place_entity 权重假设细节'
upstream_commit: '819224e506bc'
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '正式修复补丁待落'
    - 'Christian 的 place_entity 权重假设裂缝待确认'
  next_action: '落正式修复补丁（cfs_rq->curr != se 保护），Peter 复审收取'
contribution_opportunities:
  - kind: testing
    description: 'CFS_BANDWIDTH 场景复现并验证修复消除 WARNING'
  - kind: review
    description: '核查 place_entity avg_vruntime_weight 权重假设在 enqueue→dequeue 时序下的影响'
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261012-010
  - sched-20261013-008
tags: [cfs, regression]
---