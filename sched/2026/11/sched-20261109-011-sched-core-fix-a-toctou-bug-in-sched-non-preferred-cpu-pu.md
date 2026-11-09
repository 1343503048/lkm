# sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()

## TL;DR

Fushuai Wang 发单补丁修复 `sched_non_preferred_cpu_push_stop()` 的 TOCTOU 竞态：`sched_push_current_non_preferred_cpu()` 在 irq 上下文检查 `is_migration_disabled()` 后才排队 stopper，排在队列里时任务持续运行、可能在 stopper 执行前进入 `migrate_disable()`——在 stopper 里重新检查 `is_migration_disabled()` 再调 `__migrate_task()`，避免对 migrate-disabled 任务做迁移触发 `set_task_cpu` 告警。Shrikanth Hegde 追问复现方式。

## 背景与问题

`sched_push_current_non_preferred_cpu()` 在 irq 上下文把「把 current 推离非首选 CPU」的工作交给 stopper：它先检查 `is_migration_disabled()` 才排队 stopper，但排队后任务仍在运行，可能在 stopper 真正执行前进入 `migrate_disable()`。此时 `sched_non_preferred_cpu_push_stop()` 仍会对该任务调 `__migrate_task()`，触发 `WARNING: kernel/sched/core.c:3432 at set_task_cpu`（stopper 栈可见 `move_queued_task` → `sched_non_preferred_cpu_push_stop`）。属 TOCTOU（check-to-time-of-use）竞态。

## 技术方案

修复最小：在 `sched_non_preferred_cpu_push_stop()` 里、`__migrate_task()` 之前，把条件从

```c
if (task_rq(p) == rq && task_on_rq_queued(p))
```

补上一个 `!is_migration_disabled(p)` 重检，使 migrate-disabled 任务不再进入 `__migrate_task()`。改动 `kernel/sched/core.c` 1 处（+2/-1）。带 `Fixes: 74699f56ebcf`（"sched/core: Push current task from non preferred CPU"）。

## 版本演进与当前进展

*current_version: v1（2026-11-09，`<20261109083130.1679-1-fushuai.wang@linux.dev>`）*。单补丁 v1，当日 Shrikanth Hegde 回帖询问复现路径。

## Maintainer 意见与讨论焦点

- **Shrikanth Hegde**：确认性提问——「stopper 是否因此前没机会在任务设 migrate_disable 前运行？」并引用一处旧贴，请作者分享如何触发。属澄清性意见，非反对。
- 尚无维护者（Peter/Ingo）表态。

## 合入评估

*likelihood=medium*。修复方向（在 stopper 里重检 migration-disabled）符合既有模式、`Fixes:` 明确，但当日仅一条澄清性追问，未获维护者评审。*blocking_issues*：① 无维护者评审；② 复现路径待作者说明。*next_action*：作者回应 Shrikanth 的复现追问，等维护者评审收取。

## 效果评估

作者给出 WARNING 栈（`set_task_cpu+0x1b8/0xdf0`，`migration/21` stopper），未给修复后的验证数据或触发频率。属并发正确性修复，无 benchmark。

## 我可以参与的点

- **testing**：在开启 non-preferred CPU push 的平台复现该 WARNING 并验证补丁后消失。
- **review**：确认 `is_migration_disabled()` 重检在 stopper 上下文的锁/时序下是否已足够（是否有更早设置 migrate_disable 的空窗）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109083130.1679-1-fushuai.wang@linux.dev/
- Shrikanth 的追问: https://lore.kernel.org/all/3dcbccdd-0a50-4b57-b0bf-79b55911bfa2@linux.ibm.com/

---
id: sched-20261109-011
date: '2026-11-09'
subject: "sched/core: Fix a TOCTOU bug in sched_non_preferred_cpu_push_stop()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261109083130.1679-1-fushuai.wang@linux.dev>"
lore_url: "https://lore.kernel.org/all/20261109083130.1679-1-fushuai.wang@linux.dev/"
authors: [Fushuai Wang]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261109083130.1679-1-fushuai.wang@linux.dev>"
    date: '2026-11-09'
    summary: "在 sched_non_preferred_cpu_push_stop() 里重检 is_migration_disabled() 再迁移"
    review_outcome: "Shrikanth 追问复现方式，无维护者评审"
upstream_commit: null
fixes_commit: "74699f56ebcf"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "无维护者评审；复现路径待说明"
  next_action: "作者回应 Shrikanth 的复现追问，等维护者评审"
contribution_opportunities:
  - kind: testing
    description: "在开启 non-preferred CPU push 的平台复现 WARNING 并验证补丁后消失"
  - kind: review
    description: "确认重检在 stopper 锁/时序下是否已覆盖所有空窗"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 2
related_articles: []
tags: [cfs, affinity, core_sched]
---