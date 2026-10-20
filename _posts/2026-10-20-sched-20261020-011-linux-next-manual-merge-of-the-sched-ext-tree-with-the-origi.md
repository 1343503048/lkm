---
id: sched-20261020-011
date: 2026-10-20
subject: 'linux-next: manual merge of the sched-ext tree with the origin tree'
subsystem: sched
type: discussion
status: merged_tip
severity: none
thread_root_msgid: <atZM-tXvYuR1bE3z@sirena.co.uk>
lore_url: https://lore.kernel.org/all/atZM-tXvYuR1bE3z@sirena.co.uk/
authors:
- Mark Brown
maintainers_involved:
- Tejun Heo
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-next
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 无需进一步动作：两处冲突均已在 sched_ext/for-next 由 a5ba5c61951d 解决
contribution_opportunities:
- kind: discussion
  description: 对照 a5ba5c61951d 确认下游分支的合入顺序与 scx_wait_dispatching() 位置一致
generated_at: '2026-10-21T01:30:00'
source_email_count: 4
related_articles: []
tags:
- sched_ext
title: 'linux-next: manual merge of the sched-ext tree with the origin tree'
layout: article
---

## TL;DR

linux-next 集成者 Mark Brown 报告当日 sched-ext 树与 origin 树（mainline）的两处手工合并冲突（`kernel/sched/ext/sub.c` 与 `kernel/sched/ext/ext.c`），并附上临时修复；维护者 Tejun Heo 回复两处均已在 `sched_ext/for-next` 由 commit `a5ba5c61951d`（"sched_ext: Merge branch 'for-7.3-fixes' into for-7.4"）解决，当前 for-next 可干净合入 mainline。属例行树协调，无待办。

## 背景与问题

sched_ext 树（Tejun Heo 维护）与 mainline（origin 树）在 linux-next 集成时出现两处非平凡冲突：

- `kernel/sched/ext/sub.c`：origin 树的 `18f5c699d1d0a`（"sched_ext: Rename scx_reenq_wait_dispatching() to scx_wait_dispatching()"）与 sched-ext 树的 `cea8b60e4aee0`（"sched_ext: Move reject DSQ draining into core"）冲突。
- `kernel/sched/ext/ext.c`：origin 树的 `2935062be7711`（"sched_ext: Wait for SCX_OPSS_DISPATCHING before moving tasks off DSQs"）与 sched-ext 树的 `efa7bc7d71955`（"sched_ext: Avoid relocking DSQ during remote consumption"）冲突。

Mark Brown 按惯例临时修复并提示「提交给 upstream 时应向维护者提及此类非平凡冲突」。

## 技术方案

无补丁。Mark Brown 给出 `diff --cc` 临时合并（主要涉及 `scx_wait_dispatching()` 的插入位置与 `SCX_ENQ_PREEMPT_LAZY` 标志）。Tejun 指出两处均已在 `sched_ext/for-next` 由 `a5ba5c61951d`（把 for-7.3-fixes 合入 for-7.4）解决；其中 `ext.c` 冲突与 Mark 的临时合并有一处差异——`unlink_dsq_and_switch_rq_lock()` 里 `scx_wait_dispatching()` 应在清除 `p->scx.dsq` **之后**而非之前。

## 版本演进与当前进展

*current_version: null*（树协调报告，无补丁版本）。当日报告 + 维护者确认已解决。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）逐条确认：两处冲突均已在 for-next 由 `a5ba5c61951d` 解决；当前 for-next（24c453aa8598）可干净合入 mainline；并修正 Mark 临时合并中 `scx_wait_dispatching()` 在 `unlink_dsq_and_switch_rq_lock()` 里的调用顺序。无争议。

## 合入评估

*likelihood=unknown*（非寻求合入的补丁系列，属例行树协调；冲突本身已解决）。*blocking_issues*：无（已解决）。*next_action*：无需进一步动作；sched-ext 树提交合并时注意向 Linus 提及此类冲突即可。

## 效果评估

无效果数据。信息价值在于：确认 sched-ext 树与 mainline 的合并冲突已被维护者在 for-next 内部消化，不影响 sched-ext for-7.4 pull（见本日 012）。

## 我可以参与的点

- `discussion`：如自行维护 sched-ext 下游分支，可对照 `a5ba5c61951d` 与今日两个 `diff --cc`，确认本地合入顺序与 `unlink_dsq_and_switch_rq_lock()` 中 `scx_wait_dispatching()` 的位置一致。

## 参考链接

- Mark Brown 报告（sub.c）：https://lore.kernel.org/all/atZM-tXvYuR1bE3z@sirena.co.uk/
- Mark Brown 报告（ext.c）：https://lore.kernel.org/all/atZM9nFiaMvuX9kP@sirena.co.uk/
- Tejun 回复（已解决）：https://lore.kernel.org/all/16f993e261e43155c853c62c3e2d3507@kernel.org/
