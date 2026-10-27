# sched/rt,dl: Remove unreachable migration-disabled push checks

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261020-009（v2）：Shubhang Kaushik（Ampere）清理 `push_rt_task()`/`push_dl_task()` 里不可达的 migration-disabled 分支，并移除只服务该分支的 `@pull` 参数；Christian Loehle 给 `Tested-by`（「cannot reproduce the code path」），Kayra Cizmeci 给 `Reviewed-by`。
- sched-20261027-009（今天）：作者回帖感谢两位 reviewer，决定 v2 保持不动，等「当初为何引入该 fallback」的历史依据确认后再决定是否 resend。

## 背景与问题
（承接 20261020-009）`push_rt_task()` 用 `pick_next_pushable_task()` 选 `next_task`（不返回 migration-disabled 任务），`find_lock_lowest_rq()` 掉锁重取后重新检查并拒绝状态变化任务，故 push 侧的 migration-disabled fallback 不可达。v2 删除 RT/DL 两处死代码与 `@pull` 参数，属代码清理、无行为变化。

## 技术方案
（承接，今日无新补丁）删除不可达分支与 `@pull` 参数。

## 版本演进与当前进展
*current_version: v2*（`<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>`）。作者确认暂不 respin。

## Maintainer 意见与讨论焦点
Christian Loehle（Arm）`Tested-by`、Kayra Cizmeci `Reviewed-by`，两人均独立确认同一不变量（`pick_next_pushable_task()` 不可能返回 migration-disabled 任务）。作者仍想等对「这段代码当初为何引入」的历史结论，避免删错。暂无 maintainer（RT/DL 维护者）直接表态。

## 合入评估
*likelihood=medium*。两位 reviewer 背书、属低风险清理，但缺 RT/DL 维护者 Ack，作者也在等 fallback 历史依据。*blocking_issues*：fallback 历史依据待查、缺 RT/DL 维护者 Ack。*next_action*：等历史依据或维护者收取后进入 tip/sched/core。

## 效果评估
纯死代码清理，无性能数据。

## 我可以参与的点
- *kind: review*：追溯 migration-disabled fallback 的引入历史（git blame），确认删后无回归风险。

## 参考链接
- 线程: https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/

---
id: sched-20261027-009
date: 2026-10-27
subject: 'sched/rt,dl: Remove unreachable migration-disabled push checks'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>'
lore_url: 'https://lore.kernel.org/all/20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org/'
authors:
  - 'Shubhang Kaushik'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: '<20261014-sched-rt-dead-md-push-v1-1-5f9757be3c80@gentwo.org>'
    date: 2026-10-14
    summary: '仅删 RT 侧不可达 push path'
    review_outcome: '扩展为 RT+DL 两处'
  - version: v2
    msgid: '<20261014-sched-rt-dead-md-push-v2-1-9f57f1a530dc@gentwo.org>'
    date: 2026-10-15
    summary: '删 RT/DL 两处死代码与 @pull 参数'
    review_outcome: 'Christian Tested-by、Kayra Reviewed-by'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'fallback 历史依据待查'
    - '缺 RT/DL 维护者 Ack'
  next_action: '等历史依据或维护者收取后进入 tip/sched/core'
contribution_opportunities:
  - kind: review
    description: '追溯 migration-disabled fallback 引入历史，确认删后无回归风险'
generated_at: '2026-10-28T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261020-009
tags:
  - rt
  - deadline
---