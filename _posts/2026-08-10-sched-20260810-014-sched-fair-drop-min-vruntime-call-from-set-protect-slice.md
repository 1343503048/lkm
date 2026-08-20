---
subject: 'sched/fair: Drop min_vruntime() call from set_protect_slice()'
id: sched-20260810-014
date: 2026-08-10
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: <20260810145422.xxxxxx-kayra@kernel.org>
lore_url: 未获取到
authors:
- Kayra Cizmeci
- Zhan Xusheng
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
- K Prateek Nayak
current_version: v1
patch_series:
- version: v1
  msgid: <20260810145422.xxxxxx-kayra@kernel.org>
  date: 2026-08-10
  summary: Kayra 提案：从 set_protect_slice() 中去掉 min_vruntime() 调用，因该比较总是取计算值（更小）。Zhan
    Xusheng 在 8/10 反驳：在自定义 slice 场景下 @vprot 可能越过 se->deadline，盲目赋值会让 protect_slice
    在 deadline 之后仍保护实体（破坏 RUN_TO_PARITY）。
  review_outcome: Zhan 的回复表明该简化在自定义 slice + PLACE_DEADLINE_INITIAL 默认开启下不安全，提案大概率需撤回/修正。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Zhan 已指出在自定义 slice 场景下会破坏 deadline/protect 语义
  next_action: 等待作者回应 Zhan 的反例，预计需要修正或撤回 min_vruntime 简化。
contribution_opportunities:
- kind: discussion
  description: 参与 set_protect_slice 中 vprot/deadline 语义的讨论。
- kind: review
  description: 评审在自定义 slice 场景下 vprot 越过 deadline 的后果。
generated_at: '2026-08-11T00:15:00'
source_email_count: 2
related_articles: []
tags:
- sched/fair
- eevdf
title: 'sched/fair: Drop min_vruntime() call from set_protect_slice()'
layout: article
---

## TL;DR
Kayra Cizmeci 提案从 `set_protect_slice()` 去掉 `min_vruntime()` 调用，但 Zhan Xusheng 在 8/10 给出反例：在自定义 slice 场景下盲目赋值会让 `protect_slice` 在实体 deadline 之后仍保护之，破坏 RUN_TO_PARITY。提案大概率需修正/撤回。

## 背景与问题
EEVDF 的 `set_protect_slice()` 通过 `vprot`（保护虚拟截止时间）决定实体是否受保护（RUN_TO_PARITY）。原代码用 `min_vruntime()` 取计算值与既有值的最小值。Kayra 认为「计算值更小，min 总是取计算值」，于是提案去掉 min 调用。

## 技术方案（提案与反驳）
- Kayra 提案：直接把 `@vprot` 赋为计算值，省略 min。
- Zhan 反驳：`@vprot` 的论证要求其为 `se->vruntime + calc_delta_fair(se->slice, se)`，但 `se->deadline` 在 `PLACE_DEADLINE_INITIAL`（默认开启）下仅半 slice 提前；当 `cfs_rq_min_slice()` 低于 `se->slice` 且高于其一半时，`se->vruntime + calc_delta_fair(slice, se)` 会越过 `se->deadline`，此时 `min_vruntime()` 正是把 `@vprot` 钳制在 deadline 内的关键。盲目赋值会把 `se->vprot` 推过 deadline，而 `protect_slice()` 只比较 `se->vruntime` 与 `se->vprot`，导致 RUN_TO_PARITY 在 deadline 之后仍保护实体。

## 版本演进与当前进展
当前 v1 提案 + Zhan 的反例回复。尚未有修订。

## Maintainer 意见与讨论焦点
核心争议即 Zhan 指出的自定义 slice 场景下语义破坏。提案需回应此反例。

## 合入评估
合入可能性 low。存在明确反例，需作者修正或撤回。

## 效果评估
无 benchmark；属 EEVDF 保护语义正确性问题。

## 我可以参与的点
- 构造自定义 slice 场景验证 vprot 越过 deadline 的后果；
- 评审 min_vruntime 保留的必要性。

## 参考链接
- lore: 未获取到
