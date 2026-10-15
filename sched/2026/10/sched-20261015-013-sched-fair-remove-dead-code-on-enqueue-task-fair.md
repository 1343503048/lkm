# sched/fair: remove dead code on enqueue_task_fair()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261012-010：Kayra 的「remove dead code on enqueue_task_fair()」已合入 tip/sched/core（819224e506bc），但引入 CFS_BANDWIDTH 回归（throttle→dequeue→unthrottle→enqueue 命中被删分支触发 WARNING）；Peter 给出 `if (cfs_rq->curr != se) __enqueue_entity()` 修复 diff。
- sched-20261013-008：Peter 解释修复后仍只有一处 `place_entity()`（带 `ENQUEUE_QUEUED`），不构成 lag 双计；Kayra 追问 Christian 的担忧点。
- sched-20261014-007：Christian 确认 Peter 的解释，但指出 `place_entity()` 里 `avg_vruntime_weight()` 的权重项仍按「se 尚未计入」计算，具体时序是否双计待定。
- sched-20261015-013（今天）：Peter 表示再往下改会「更乱」，明确「Feel free to send a revert that includes a comment」；Kayra 随即发 Revert 补丁（带 CFS_BANDWIDTH 注释），并补一处 `place_entity()` 在 `curr==se` 时的处理。

## 背景与问题
（承接 20261012-010 → 20261014-007）原「dead code」补丁删除了 `enqueue_task_fair()` 里被认为不可达的 `cfs_rq->curr == se` 分支；CFS_BANDWIDTH 下任务 throttle 后、schedule out 前又 wakeup，`cfs_rq->curr` 仍是它而 `on_rq` 为 false，unthrottle 重新 enqueue 该 curr 命中被删分支触发 WARNING。今天讨论收口为该补丁引入的回归与其修复方式。

## 技术方案
（承接 20261012-010/20261014-007）Peter 今日表态：与其继续就地打补丁（他自己改会「make it a bigger mess」），不如回退。Kayra 的 Revert（<20261015082919.4344-1-kayracizmeci@gmail.com>，kernel/sched/fair.c +15/−3）：
- 恢复 `curr = (cfs_rq->curr == se)` 判断与注释，文档化「CFS_BANDWIDTH 下任务可被 throttle+dequeue、再从别的 CPU unthrottle、又在 schedule() 前重新 enqueue」这条真实路径。
- `if (curr) place_entity(cfs_rq, se, flags);` 先行；
- 随后用 `if (!curr) { ... }` 包裹 `enqueue_hierarchy / reweight / __enqueue_entity`，避免对 curr 重复 enqueue。
- `Fixes: 819224e506bc`，`Reported-by: Christian Loehle`。

Kayra 自述「Killing my own beast :-)，Not tested at all」。

## 版本演进与当前进展
- 原补丁（已合入 819224e506bc）→ Peter 修复 diff（20261012-010）→ 今日 Peter 拍板回退 → Kayra 发 Revert 补丁。

## Maintainer 意见与讨论焦点
Peter Zijlstra 明确授权回退：「I'm not seeing one at the moment; that is, I end up making it a bigger mess. Feel free to send a revert that includes a comment about this.」即维护者倾向 revert + 注释而非继续就地修复。遗留点：Revert 未测试（作者自述）；以及是否彻底解决 20261014-007 里 Christian 提出的 `place_entity()` 权重双计细节。

## 合入评估
*likelihood=high*。维护者已明确指示 revert 方向、作者已照做，路径清晰。*blocking_issues*：Revert 未测试；需 Peter 最终收取。*next_action*：作者补测试（或至少说明验证）、等 Peter 合入，并回应 Christian 的权重双计问题。

## 效果评估
无量化数据。这是回归修复（消除 CFS_BANDWIDTH 下 WARNING），作者未测试，故暂无验证结果。

## 我可以参与的点
- *testing*：按 20261012-010 描述的 CFS_BANDWIDTH throttle/unthrottle 时序复现 WARNING，验证 Revert 补丁消除 WARNING且无新回归。
- *review*：确认 Revert 后 `place_entity()` 的权重项（Christian 20261014-007 的疑问）是否仍存在双计边缘。

## 参考链接
- Revert 补丁：https://lore.kernel.org/all/20261015082919.4344-1-kayracizmeci@gmail.com/
- Peter 的回退授权：https://lore.kernel.org/all/20261015074922.GM2009045@noisy.programming.kicks-ass.net/
- Kayra 的提问：https://lore.kernel.org/all/20261015074238.2363-1-kayracizmeci@gmail.com/

---
id: sched-20261015-013
date: 2026-10-15
subject: "sched/fair: remove dead code on enqueue_task_fair()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261015082919.4344-1-kayracizmeci@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261015082919.4344-1-kayracizmeci@gmail.com/"
authors: ["Kayra Cizmeci"]
maintainers_involved: ["Peter Zijlstra"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261015082919.4344-1-kayracizmeci@gmail.com>"
    date: 2026-10-15
    summary: "Revert 819224e506bc，恢复 cfs_rq->curr==se 分支并加 CFS_BANDWIDTH 注释"
    review_outcome: "Peter 授权 revert，Kayra 已发，未测试"
upstream_commit: null
fixes_commit: "819224e506bc"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Revert 未测试"]
  next_action: "作者补测试说明、等 Peter 合入，并回应权重双计疑问"
contribution_opportunities:
  - kind: testing
    description: "复现 CFS_BANDWIDTH WARNING 并验证 Revert 消除且无新回归"
  - kind: review
    description: "确认 Revert 后 place_entity() 权重项是否仍存双计边缘"
generated_at: "2026-10-16T01:05:00"
source_email_count: 3
related_articles: ["sched-20261012-010", "sched-20261013-008", "sched-20261014-007"]
tags: [cfs, eevdf, regression]
---