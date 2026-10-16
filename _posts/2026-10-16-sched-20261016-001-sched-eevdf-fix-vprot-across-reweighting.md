---
id: sched-20261016-001
date: 2026-10-16
subject: 'sched/eevdf: Fix vprot across reweighting'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261016153721.7843-1-kayracizmeci@gmail.com>
lore_url: https://lore.kernel.org/all/20261016153721.7843-1-kayracizmeci@gmail.com/
authors:
- Kayra Cizmeci
maintainers_involved:
- Vincent Guittot
current_version: v5
patch_series:
- version: v3
  msgid: <20261016084604.17999-1-kayracizmeci@gmail.com>
  date: 2026-10-16
  summary: 初始修复：reweight_eevdf 跟随 vruntime 平移 vprot，!curr 路径扩展 protection
  review_outcome: Vincent 认可部分但认为逻辑散布、要求收敛
- version: v4
  msgid: <20261016150402.6952-1-kayracizmeci@gmail.com>
  date: 2026-10-16
  summary: sched_change_end() 路径改为 active 时 cancel protection，重算收敛回 reweight_eevdf()
  review_outcome: Vincent「looks good for me」
- version: v5
  msgid: <20261016153721.7843-1-kayracizmeci@gmail.com>
  date: 2026-10-16
  summary: 采用 Vincent 的注释文案、收下 Reviewed-by
  review_outcome: Vincent Reviewed-by
upstream_commit: null
fixes_commit: 80390ead2080
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Peter Zijlstra 收取合入，或作者补充运行时测试
contribution_opportunities:
- kind: testing
  description: 验证 sched_change 路径下 vprot 与 vruntime 的转换一致性及 cancel_protect_slice 触发
generated_at: '2026-10-17T01:30:00'
source_email_count: 11
related_articles: []
tags:
- eevdf
- cfs
title: 'sched/eevdf: Fix vprot across reweighting'
layout: article
---

## TL;DR
Kayra Cizmeci 修复 EEVDF 中「vprot（slice protection）在 reweighting 时可能出错」的 bug：任务 vruntime 改变时，已死掉的 protection 可能复活、或活着的 protection 增减甚至死掉，破坏保护切片的正确性。当天 v3→v4→v5 快速迭代，Vincent Guittot 全程 review 并最终给出 Reviewed-by，v5 已收敛，等 Peter 收取。

## 背景与问题
`reweight_eevdf()` 在任务权重（priority/weight）改变时重算 deadline、vruntime 等，但 `vprot`（EEVDF slice protection 的保护点，见 `bcd74b2ffdd0`「Only set slice protection at pick time」）没有被一致地跟随 vruntime 平移，导致「dead protection 可能复活、alive protection 可能增减甚至死掉」。作者给两处 `Fixes:`：`80390ead2080 ("sched/fair: Separate se->vlag from se->vprot")` 与 `bcd74b2ffdd0 ("sched/fair: Only set slice protection at pick time")`。这是 EEVDF 正确性问题，不是性能优化。

## 技术方案
最终 v5 形态（`kernel/sched/fair.c`，+13/−2）分两处：

- `reweight_eevdf()` 的 `on_rq` 分支里：`rel_vprot` 时 `se->vprot += avruntime`；否则若 `curr`，`se->vprot = se->vruntime`。
- `enqueue_task_fair()` 的 `!curr` 路径里：`place_entity()` 之后，若 `task_current_donor(rq, p)` 则 `cancel_protect_slice(se)`（带注释说明 `sched_change` 模式下 `cfs_rq->curr == NULL` 但 `rq->donor == p`）。

关键设计取舍来自 Vincent Guittot 的 review 引导：**不要试图在所有路径上让 vprot 完全正确**——「trying to keep vprot correct in all cases is not worth the effort, nor is it achievable without cost」。改 prio/slice 后任务本就不一定还是最优选择，正确做法是 best-effort：要么跟随重算、要么直接取消/缩减保护，确保不会拿到过长的保护切片。

## 版本演进与当前进展
- v3（<20261016084604.17999-1-kayracizmeci@gmail.com>）：初始修复，在 `enqueue_task_fair()` 的 `!curr` 路径内做 protection 扩展，被 Vincent 评价「spread this all over the code」不优雅。
- v4（<20261016150402.6952-1-kayracizmeci@gmail.com>）：按 Vincent 意见，`sched_change_end()` 路径不再扩展 protection，改为 active 时直接 cancel；把重算收敛回 `reweight_eevdf()` 内。
- v5（<20261016153721.7843-1-kayracizmeci@gmail.com>）：采用 Vincent 给的注释文案、收下 tag（`Reviewed-by: Vincent Guittot`）。作者自述仍「Not tested」。

## Maintainer 意见与讨论焦点
Vincent Guittot 逐版 review，态度从「this part looks good」「但 `se != curr` 为何需要」到给出自己的重构建议，再到「yes, looks good for me」最终 Reviewed-by。核心分歧已在 v3→v4 解决：Vincent 反对把 vprot 修正逻辑散布到各调用点，主张收敛在 `reweight_eevdf()`、`sched_change` 路径只做 cancel。

## 合入评估
*likelihood=high*。已获 Vincent Guittot 的 Reviewed-by，方案与实现形态收敛，无实质阻塞。*blocking_issues*：无。*next_action*：等 Peter Zijlstra 收取合入（或作者补充真实测试后提交）。

## 效果评估
作者连续标注「Not tested at all」/「Compile tested only」/「Not tested」，无任何运行时验证或量化数据。属正确性修复，效果为逻辑推演，未见测试数据。

## 我可以参与的点
- *testing*：作者明言未测试。可在本地验证 `sched_change` 路径（`sched_setattr()` 改变 weight/priority）下 `vprot` 的转换是否与 `vruntime` 一致，以及 `cancel_protect_slice()` 在 `!curr` 且 `task_current_donor()` 为真时是否正确触发。

## 参考链接
- v5：https://lore.kernel.org/all/20261016153721.7843-1-kayracizmeci@gmail.com/
- v4：https://lore.kernel.org/all/20261016150402.6952-1-kayracizmeci@gmail.com/
- v3：https://lore.kernel.org/all/20261016084604.17999-1-kayracizmeci@gmail.com/
- Vincent 的最终 Reviewed-by：https://lore.kernel.org/all/CAKfTPtB04o_WSw5AXfwtPYizJwBUja3XzMrmQJUk5XXqqpvuhA@mail.gmail.com/
