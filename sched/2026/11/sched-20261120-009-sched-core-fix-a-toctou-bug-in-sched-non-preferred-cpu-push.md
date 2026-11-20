# sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261109-011：Fushuai Wang 发 v1 修 `sched_non_preferred_cpu_push_stop()` 的 TOCTOU 竞态；Shrikanth 追问复现。
- sched-20261118-008：v2 发出，补全竞态时序与 WARNING 栈，Shrikanth 给 Reviewed-by。
- sched-20261120-009（今天）：**v3 发出**——v2→v3 无代码改动，仅按建议给新增检查加注释；带 `Suggested-by: Peter Zijlstra`、`Reviewed-by: Shrikanth Hegde`、`Fixes: 74699f56ebcf`。处于可收取状态。

## 背景与问题

（承接 sched-20261109-011 / 20261118-008）`sched_push_current_non_preferred_cpu()` 在 irq 上下文先查 `is_migration_disabled()` 再排队 stopper，而 `migrate_disable()` 在 `preempt_disable()` 段内才设 `p->migration_disabled = 1`，irq 可落在两者之间——排队时读到「尚未 migrate-disabled」的旧值，stopper 执行时任务却已 migrate-disabled，若仍 `__migrate_task()` 就触发 `set_task_cpu` 的 WARNING（复现栈见 v2：`set_task_cpu` ← `move_queued_task` ← `sched_non_preferred_cpu_push_stop`）。

## 技术方案

在 `sched_non_preferred_cpu_push_stop()` 里、`__migrate_task()` 之前重检 `!is_migration_disabled(p)`，使 migrate-disabled 任务不再进入迁移路径。v3 与 v2 相同（`kernel/sched/core.c` +7/-1），仅给该检查补说明竞态缘由的注释。

## 版本演进与当前进展

*current_version: v3（2026-11-20，`<20261120051742.50358-1-fushuai.wang@linux.dev>`，单补丁）*。v1→v2 改进 commit message；v2→v3 加注释、无代码改动。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：`Suggested-by`（提出重检方案）。
- **Shrikanth Hegde（IBM，评审）**：`Reviewed-by`。
- 无 NAK；补丁已收敛到「可收取」状态，等 maintainer 收取。

## 合入评估

*likelihood=high*。TOCTOU 修复逻辑清晰、带 `Suggested-by`(Peter)+`Reviewed-by`(Shrikanth)+`Fixes` tag，无未决分歧。*blocking_issues*：无实质阻塞，等维护者收取。*next_action*：Peter/Ingo 收取进 tip/sched/core。

## 效果评估

正确性修复；作者给出 v7.4.0-rc1 上的 WARNING 复用栈作为复现证据，未提供量化数据。

## 我可以参与的点

- **review**：核对重检 `is_migration_disabled()` 的时序是否覆盖「排队后、stopper 前」的全部竞态窗口，以及注释准确性。

## 参考链接

- lore thread（v3）: https://lore.kernel.org/all/20261120051742.50358-1-fushuai.wang@linux.dev/

---
id: sched-20261120-009
date: '2026-11-20'
subject: "sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261120051742.50358-1-fushuai.wang@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261120051742.50358-1-fushuai.wang@linux.dev/"
authors: [Fushuai Wang]
maintainers_involved: [Peter Zijlstra]
current_version: v3
patch_series:
  - version: v1
    msgid: "<20261109013952.71400-1-fushuai.wang@linux.dev>"
    date: '2026-11-09'
    summary: "stopper 里重检 is_migration_disabled 后再 __migrate_task"
    review_outcome: "Shrikanth 追问复现"
  - version: v2
    msgid: "<20261118065921.98260-1-fushuai.wang@linux.dev>"
    date: '2026-11-18'
    summary: "补全竞态时序与 WARNING 栈"
    review_outcome: "Shrikanth Reviewed-by"
  - version: v3
    msgid: "<20261120051742.50358-1-fushuai.wang@linux.dev>"
    date: '2026-11-20'
    summary: "无代码改动，仅加注释"
    review_outcome: "待维护者收取"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Peter/Ingo 收取进 tip/sched/core"
contribution_opportunities:
  - kind: review
    description: "核对重检时序是否覆盖排队后/stopper 前的全部竞态窗口"
generated_at: "2026-11-21T09:00:00+08:00"
source_email_count: 216
related_articles: [sched-20261109-011, sched-20261118-008, sched-20261119-003]
tags: [core_sched, preempt]
---