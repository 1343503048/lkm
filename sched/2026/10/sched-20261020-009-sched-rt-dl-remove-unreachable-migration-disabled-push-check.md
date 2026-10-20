# sched/rt,dl: Remove unreachable migration-disabled push checks

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261015-008：Shubhang Kaushik（Ampere）v2 清理 `push_rt_task()`/`push_dl_task()` 里不可达的 migration-disabled 分支（候选由 `pick_next_pushable_task()` 选出、本就跳过 migration-disabled 任务），并移除只服务该分支的 `@pull` 参数；无行为变化，v2 刚发暂无 review。
- sched-20261019-009：Christian Loehle（Arm）回帖「FWIW I also cannot reproduce the code path」并给 `Tested-by`，同时表示还想说服自己这确实成立、或查清这段代码当初为何引入。
- sched-20261020-009（今天）：Kayra Cizmeci 给出 `Reviewed-by`，并重申「`pick_next_pushable_task()` 不会返回 `is_migration_disabled()` 为真的任务」，认为该检查确实永假。

## 背景与问题

（承接 20261015-008 → 20261019-009）`push_rt_task()` 用 `pick_next_pushable_task()` 选 `next_task`（不返回 migration-disabled 任务），`find_lock_lowest_rq()` 掉锁重取后重新检查并拒绝状态变化任务，故 push 侧的 migration-disabled fallback 不可达。v2 删除 RT/DL 两处死代码与 `@pull` 参数，属代码清理。

## 技术方案

（承接，今日为 review 反馈，无新补丁）第二位 reviewer Kayra Cizmeci 独立确认同一不变量：`pick_next_pushable_dl_task()` 已不可能返回 `is_migration_disabled()` 为真的任务，故该检查「never true」，给出 `Reviewed-by`。

## 版本演进与当前进展

*current_version: v2*。v2（20261014 发出）已有两位 reviewer 背书：Christian Loehle（Tested-by，20261019）+ Kayra Cizmeci（Reviewed-by，今日）。

## Maintainer 意见与讨论焦点

Kayra Cizmeci（今日）：`Reviewed-by`，并独立论证「`pick_next_pushable_task()` 不返回 migration-disabled 任务、该检查永假」。Christian Loehle（前日）持保留式 Tested-by（仍在「说服自己」）。RT/DL 维护者（Steven Rostedt、Juri Lelli）仍未表态。

## 合入评估

*likelihood=unknown*。已有 Tested-by 与 Reviewed-by 两份独立背书，但论证的不变量尚未获 RT/DL 维护者确认。*blocking_issues*：RT/DL 维护者无表态。*next_action*：等 Steven Rostedt/Juri Lelli 确认死代码判断即可合入。

## 效果评估

无性能差异（死代码清理）。两位 reviewer 均为「无法复现该路径 / 检查永假」的否定性验证，无负面行为证据。

## 我可以参与的点

- `review`：独立验证「push 侧 migration-disabled fallback 不可达」论证的完整性，特别是 `find_lock_lowest_rq()` 掉锁重取后的重检查是否覆盖全部路径，替 RT/DL 维护者补上那一步确认。

## 参考链接

- Kayra 今日回帖：https://lore.kernel.org/all/atZR51V-xwaRL6OL@scheduler.schedules/
- v2 patch：https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/

---
id: sched-20261020-009
date: 2026-10-20
subject: "sched/rt,dl: Remove unreachable migration-disabled push checks"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
lore_url: "https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/"
authors: ["Shubhang Kaushik"]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org>"
    date: 2026-10-14
    summary: "删除 push_rt_task() 不可达的 migration-disabled fallback 与 @pull 参数"
    review_outcome: "暂无 review"
  - version: v2
    msgid: "<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>"
    date: 2026-10-14
    summary: "扩展删除 push_dl_task() 的对应检查"
    review_outcome: "Christian Loehle Tested-by（保留式）、Kayra Cizmeci Reviewed-by"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: ["RT/DL 维护者（Steven Rostedt/Juri Lelli）仍未表态"]
  next_action: "等 RT/DL 维护者确认死代码判断即可合入"
contribution_opportunities:
  - kind: review
    description: "独立验证 push 侧 migration-disabled fallback 不可达论证的完整性"
generated_at: "2026-10-21T01:30:00"
source_email_count: 1
related_articles: ["sched-20261015-008", "sched-20261019-009"]
tags: [rt, deadline]
---