---
id: sched-20261120-011
date: '2026-11-20'
subject: 'sched/fair: Always clear se->exec_start when migrated'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261120095819.1009260-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20261120095819.1009260-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261120095819.1009260-1-vincent.guittot@linaro.org>
  date: '2026-11-20'
  summary: 把 se->exec_start 清零上移到 enqueue_task_fair 入口，覆盖 throttled 迁移
  review_outcome: Kayra 追问 Fixes tag 与 changelog
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Fixes tag 与 changelog 建议待回应
  next_action: 作者补充 Fixes 后进入正常合入
contribution_opportunities:
- kind: review
  description: 核对该清零迁移位置对后续 exec_start 读取顺序的影响及 Fixes 指向
generated_at: '2026-11-21T09:00:00+08:00'
source_email_count: 216
related_articles: []
tags:
- cfs
title: 'sched/fair: Always clear se->exec_start when migrated'
layout: article
---

## TL;DR

Vincent Guittot 发单补丁：把「迁移时清 `se->exec_start`」从 `enqueue_entity()` 里的 conditional 移到 `enqueue_task_fair()` 入口，无条件处理——此前迁移到 throttled cfs_rq 的任务不会清 `exec_start`（那段清除被提前 return 跳过）。Kayra Cizmeci 追问是否需要 `Fixes` tag 与更明确的 changelog。小修复。

## 背景与问题

`enqueue_entity()` 里原有逻辑：`if (flags & ENQUEUE_MIGRATED) se->exec_start = 0;`。但当任务迁移到 throttled cfs_rq 时，`enqueue_task_fair()` 会走 `enqueue_throttled_task()` 提前返回，`enqueue_entity()` 不会被调用，`se->exec_start`（用于估算任务热度的「最近开始执行时间」）不清零，可能把迁移后的任务误判为「热任务」。

## 技术方案

把 `se->exec_start = 0` 从 `enqueue_entity()` 上移到 `enqueue_task_fair()` 入口（`task_is_throttled(p) && enqueue_throttled_task(p)` 判断之前），确保「迁移即清、含 throttled 情形」；同时删掉 `enqueue_entity()` 里那句注释「Entity has migrated, no longer consider this task hot」对应代码。净改动 4 行（`kernel/sched/fair.c`）。

## 版本演进与当前进展

*current_version: v1（2026-11-20，`<20261120095819.1009260-1-vincent.guittot@linaro.org>`，单补丁）*。首版，Kayra Cizmeci 当日追问 `Fixes` tag 与 changelog 是否更明确。

## Maintainer 意见与讨论焦点

- **Kayra Cizmeci（社区评审，非维护者）**：追补丁是否需 `Fixes` tag，并建议 changelog 写明「`se->exec_start` 未被清除导致的问题路径」。
- Vincent Guittot 系 sched/fair 维护者本人提交（联合维护者），尚未见 Peter/其他维护者表态。
- 无 NAK。

## 合入评估

*likelihood=high*。作者是 sched/fair 维护者、改动小且语义明确（修 throttled 迁移路径的清零遗漏）；仅剩 `Fixes` tag 的格式建议未回应。*blocking_issues*：Kayra 的 `Fixes` tag 与 changelog 建议待作者回应。*next_action*：作者补充（或说明）`Fixes` 后即可进入正常合入。

## 效果评估

无量化数据；属「任务热度判定」正确性修复，作者未给基准（主观描述迁移后不应视为热任务）。

## 我可以参与的点

- **review**：核对上移 `se->exec_start = 0` 后是否影响 `enqueue_task_fair()` 里 `update_stats_enqueue` 等后续对 `exec_start` 的读取顺序，以及是否应随 patch 一并给 `Fixes` 指向引入 throttled 提前返回的 commit。

## 参考链接

- lore thread（patch）: https://lore.kernel.org/all/20261120095819.1009260-1-vincent.guittot@linaro.org/
