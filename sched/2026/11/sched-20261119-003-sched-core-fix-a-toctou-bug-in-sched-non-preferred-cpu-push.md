# sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261109-011：Fushuai Wang 发 v1 修 `sched_non_preferred_cpu_push_stop()` 的 TOCTOU 竞态——`sched_push_current_non_preferred_cpu()` 在 irq 上下文先查 `is_migration_disabled()` 再排队 stopper，任务可能在 stopper 执行前进入 `migrate_disable()`；v1 在 stopper 里重检后再 `__migrate_task()`。Shrikanth 追问复现方式。
- sched-20261118-008：**v2 发出**，补全详细竞态时序（`migrate_disable()` 在 `preempt_disable()` 段内设 `p->migration_disabled`，irq 可落在两者之间）+ 完整 WARNING 栈；Shrikanth 给 Reviewed-by。
- sched-20261119-003（今天）：**Peter Zijlstra 评审 v2**——对同一竞态感叹（指向他 9/25 的同类讨论），认可方向，建议在 `sched_push_current_non_preferred_cpu()` 加注释说明「`is_migration_disabled(current)` 不稳定」，并提议在 `is_migration_disabled()` 里加 `lockdep_assert(!task_on_cpu(p) || in_task())` 以捕获更多同类竞态。

## 背景与问题

（承接 sched-20261109-011 … 20261118-008）`migrate_disable()` 在 `preempt_disable()` 段内设置 `p->migration_disabled = 1`；一个 irq 可在 `preempt_disable()` 之后、`migration_disabled = 1` 之前命中。irq 返回后任务因抢占关闭无法被 stopper 抢占，会先把 `migration_disabled = 1` 设完再轮到 stopper 运行——即排队 stopper 时读到的是「尚未 migrate-disabled」的旧值，而 stopper 执行时任务已是 migrate-disabled，若仍 `__migrate_task()` 就触发 `set_task_cpu` 的 WARNING。

## 技术方案

今日为 Peter 对 v2 的评审、无新补丁：

- Peter 认可 v2 的「stopper 里重检」修复方向，但要加注释，示例如下：
  ```c
  /*
   * Racy: is_migration_disabled(current) isn't stable.
   */
  if (is_migration_disabled(push_task))
  	return;
  ```
- 更进一步，Peter 提议在 `is_migration_disabled()` 内部加 `lockdep_assert(!task_on_cpu(p) || in_task())`，把「在原子/irq 上下文误读 migrate-disabled 状态」这类竞态变成 lockdep 可判定的类错误，便于系统性发现类似问题。
- Peter 同时指向他自己 2026-09-25 的帖子（`20260925074953.GG4121339@noisy.programming.kicks-ass.net`），说明这不是新发现的竞态、值得借本次一并固话。

## 版本演进与当前进展

*current_version: v2（2026-11-18，`<20261118065921.98260-1-fushuai.wang@linux.dev>`）*。v1 → v2：补全竞态时序与 WARNING 栈、获 Shrikanth Reviewed-by。今日 Peter 评审，建议补注释 + lockdep 断言，尚未出新版。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（调度维护者）**：认可修复，要求补「竞态说明」注释，并提议 `lockdep_assert(!task_on_cpu(p) || in_task())` 作为通用防护。
- **Shrikanth Hegde**（此前）：v2 已给 Reviewed-by。
- 无 NAK；分歧点仅是「是否把 lockdep 断言一并纳入本次补丁」的实现取舍。

## 合入评估

*likelihood=high*。修复方向获维护者认可、已有 Reviewer 背书，只差把 Peter 的两点建议（注释、可选的 lockdep 断言）落进 v3。*blocking_issues*：Peter 的注释/lockdep 建议尚未落实。*next_action*：作者出 v3 补注释（并按需加 lockdep 断言），Peter 收取。

## 效果评估

无性能数据；价值在消除 `set_task_cpu` WARNING 竞态。Peter 未否定复现路径，v2 的 WARNING 栈（承接 20261118-008）即触发证据。

## 我可以参与的点

- **review**：评估 `lockdep_assert(!task_on_cpu(p) || in_task())` 加进 `is_migration_disabled()` 后是否会误报（该函数既有调用点是否都满足断言前置条件）。
- **testing**：在开启 lockdep 的构建上跑 preferred-CPU 推挤相关路径，验证断言不误触发。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261118065921.98260-1-fushuai.wang@linux.dev/
- Peter 评审: https://lore.kernel.org/all/20261119090728.GN2668804@noisy.programming.kicks-ass.net/

---
id: sched-20261119-003
date: '2026-11-19'
subject: "sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261118065921.98260-1-fushuai.wang@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261118065921.98260-1-fushuai.wang@linux.dev/"
authors: [Fushuai Wang]
maintainers_involved: [Peter Zijlstra]
current_version: v2
patch_series:
  - version: v1
    msgid: null
    date: '2026-11-09'
    summary: "stopper 里重检 is_migration_disabled 后再 migrate"
    review_outcome: "Shrikanth 追问复现方式"
  - version: v2
    msgid: "<20261118065921.98260-1-fushuai.wang@linux.dev>"
    date: '2026-11-18'
    summary: "补全竞态时序与 WARNING 栈"
    review_outcome: "Shrikanth Reviewed-by；Peter 建议补注释 + lockdep 断言"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["Peter 的注释/lockdep 断言建议未落实"]
  next_action: "作者出 v3 补注释（按需加 lockdep 断言），Peter 收取"
contribution_opportunities:
  - kind: review
    description: "评估 lockdep_assert 加入 is_migration_disabled 是否误报"
  - kind: testing
    description: "lockdep 构建下验证 preferred-CPU 推挤路径断言不误触发"
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261109-011, sched-20261118-008]
tags: [affinity, load_balance]
---