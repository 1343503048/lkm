---
id: sched-20260929-017
date: 2026-09-29
subject: 'sched/eevdf: Compare min slice during wake_affine'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260921152238.3804392-8-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/CAKfTPtDq-JeM=_MkYyx-HfUad529qdQbkTbVhCfFCtsdFGrU7g@mail.gmail.com/
authors:
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20260921152238.3804392-8-vincent.guittot@linaro.org>
  date: 2026-09-21
  summary: wake_affine 新增 wake_affine_slice()：se->slice 小于 prev/this CPU min_slice
    时优先选该 CPU
  review_outcome: Kayra 09-27 质疑应选 min_slice 更大的 CPU；Vincent 09-29 澄清「尽量偏向 prev CPU」
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Kayra 替代 diff 是否采纳未明确
  next_action: Vincent 在后续版本明确 wake_affine_slice 的选择语义
contribution_opportunities:
- kind: discussion
  description: 结合偏 prev CPU 目标评估 Kayra 替代 diff 是否冲突或更优，给分析/小规模实测
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles:
- sched-20260927-006
tags:
- eevdf
- load_balance
title: 'sched/eevdf: Compare min slice during wake_affine'
layout: article
---

> **subject**：`sched/eevdf: Compare min slice during wake_affine`

## TL;DR

本文为增量更新，完整脉络见 related_articles（Vincent Guittot 的 8 补丁「Improving latency of short slice tasks」系列中的 patch 7/8）。

- <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>：系列 v1 发出，patch 7/8 在 wake_affine 阶段新增 `wake_affine_slice()`，检查唤醒 CPU 是否会因自身 slice 更长而被抢占。
- <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-006-sched-eevdf-compare-min-slice-during-wake-affine.html">sched-20260927-006</a>：Kayra Cizmeci 提 review 疑问——现行逻辑在 `se->slice` 小于某 CPU 的 min_slice 时优先选该 CPU，Kayra 认为「落到 min_slice 更大的 CPU 更好」并给替代 diff。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-017-sched-eevdf-compare-min-slice-during-wake-affine.html">sched-20260929-017</a>（今天）：Vincent Guittot 回复澄清——「For wake affine, we try to favor prev cpu if possible」，即 wake_affine 阶段的目标是「尽量偏向 prev CPU」，间接回应了 Kayra 的方向性疑问。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/27/sched-20260927-006-sched-eevdf-compare-min-slice-during-wake-affine.html">sched-20260927-006</a>）EEVDF 下短 slice 任务的 CPU 选择阶段（`select_task_rq_fair`/`wake_affine`）此前不考虑 min slice，短 slice 任务可能被放到会先运行长 slice 任务（被立即抢占）的 CPU 上。patch 7/8 在 wake_affine 里加入 min slice 判断。今天无新背景，进展是作者对 Kayra 疑问的一句话澄清。

## 技术方案

（承接）patch 7/8 的 `wake_affine_slice()` 比较 `se->slice` 与 prev/this CPU 的 `get_rq_min_slice()`。今天 Vincent 未给代码，仅澄清设计意图：wake_affine 阶段的原则是「尽量偏向 prev CPU（如果可能）」，即 Kayra 提的「选 min_slice 更大的 CPU」并不一定是该阶段的优化目标——该阶段更在意避免唤醒任务被放到会被立即抢占的位置（进而保住 prev CPU 的亲和/缓存友好）。

## 版本演进与当前进展

- v1（2026-09-21，patch 7/8 `<20260921152238.3804392-8-vincent.guittot@linaro.org>`）。
- 09-27：Kayra 提疑问 + 替代 diff。
- 09-29：Vincent 一句话澄清（`<CAKfTPtDq-JeM=_MkYyx-HfUad529qdQbkTbVhCfFCtsdFGrU7g@mail.gmail.com>`）。

## Maintainer 意见与讨论焦点

- **Vincent Guittot**（作者/维护者）：澄清 wake_affine 阶段「尽量偏向 prev CPU」，回应 Kayra 的前一日疑问。
- **Kayra Cizmeci**（前一日）：质疑「落到 min_slice 更大的 CPU 更好」并给替代 diff。今日尚未见其对 Vincent 澄清的进一步回应。
- 结论性不强：一句话澄清指出了方向（偏 prev CPU），但 Kayra 的替代 diff 是否被采纳/否决仍未明确展开。

## 合入评估

*likelihood=unknown*（就本 patch 而言）。Vincent 已回应 Kayra 的疑问、但尚未给出是否采纳替代 diff 的明确结论，实现层面是否调整待后续。*blocking_issues*：Kayra 替代 diff 是否采纳未明确；与 8/8 的调整一并待定。*next_action*：Vincent 在后续版本中明确 wake_affine_slice 的选择语义（是否折入 Kayra 的意见）。

## 效果评估

本 patch 无单独效果数据；系列整体 benchmark 见 <a class="article-ref" href="/lkm/2026/09/21/sched-20260921-001-improving-latency-of-short-slice-tasks.html">sched-20260921-001</a>。

## 我可以参与的点

- `discussion`：结合「偏 prev CPU」的目标，评估 Kayra 的替代 diff（选 min_slice 更大者）是否与之冲突或在某些负载下更优，给出分析或小规模 cyclictest 对照。

## 参考链接

- lore（patch 7/8）: https://lore.kernel.org/all/20260921152238.3804392-8-vincent.guittot@linaro.org/
- lore（Vincent 澄清）: https://lore.kernel.org/all/CAKfTPtDq-JeM=_MkYyx-HfUad529qdQbkTbVhCfFCtsdFGrU7g@mail.gmail.com/
