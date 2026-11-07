# sched_ext: Reset task fields on exit of an SCX_TASK_READY task

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261106-015：Rahad Bhuiya 的 1 行修复（sched_ext）补上 `scx_reset_task_fields()` 的一个漏调用：任务以 `SCX_TASK_READY` 状态退出时 `__scx_disable_and_exit_task()` 在状态机 switch 里直接 break 而不复位其 SCX 管理字段，违反「任务离开调度器控制后状态干净」的不变式。`Fixes:` 指向 `a298fd5f4ee8`。当日无评审。
- sched-20261107-007（今天）：**Tejun Heo 回复「Applied to sched_ext/for-7.4-fixes」**，修复合入。同日 Tejun 另在 bpf-next 版本线程给出长篇解释——说清为什么 `SCX_TASK_READY` 退出路径必须复位：RT/DL 任务与非 SCHED_EXT 任务总处于 READY 状态，其 BPF 代码仍可写 `dsq_vtime`/`slice`，不复位就会随任务迁移到另一个 sched 而泄漏。

## 背景与问题

（承接 sched-20261106-015）commit `a298fd5f4ee8` 把 SCX 管理字段复位抽到 `scx_reset_task_fields()`，但 `__scx_disable_and_exit_task()` 的 `SCX_TASK_READY` 分支仍是空 break，这类任务退出时字段不复位。

今日 Tejun 的补充解释把必要性讲得更透：一个 READY 任务在 sched 上、但位于 ext 类之外——RT/DL 任务永远如此，部分切换下的非 SCHED_EXT 任务也如此。sched 的 BPF 代码仍能写这类任务的 `dsq_vtime` 和 `slice`；因为 READY 退出路径不复位它们，当任务迁移到另一个 sched（例如一个 RT 任务从 sub-sched A 的 cgroup 移到 sub-sched B 的 cgroup，之后转 SCHED_NORMAL）时，B 的 `ops.enable()` 会看到从 A 那里带过来的 `dsq_vtime` 残留。

## 技术方案

（承接）在 `__scx_disable_and_exit_task()` 的 `case SCX_TASK_READY:` 里补上 `scx_reset_task_fields(task_rq(p), p)`，与其它退出路径一致。改动 `kernel/sched/ext/ext.c` 仅 +1 行。`Fixes:` 指向 `a298fd5f4ee8`。

## 版本演进与当前进展

*current_version: v1（2026-11-06 发出）*。今日 Tejun Heo 应用并回复，无新版本。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）认同修复方向：在 bpf-next 版本线程给出长篇机理说明（READY 任务的 `dsq_vtime`/`slice` 残留会跨 sched 泄漏），随即在 `[PATCH v2]` 线程回复「Applied to sched_ext/for-7.4-fixes」。无 NAK，无争议。

## 合入评估

*likelihood=merged*。已合入 sched_ext/for-7.4-fixes 分支。*blocking_issues*：无。*next_action*：观察是否随 for-7.4-fixes 进入下一周期主线回合；如需回 stable 可评估。

## 效果评估

无性能数据。效果为不变式恢复：`SCX_TASK_READY` 退出路径的管理字段（`dsq_vtime`、`slice`、reenqueue flags、watchdog `runnable_at`）得到复位，避免残留状态跨 sched 污染。

## 我可以参与的点

当前阶段暂无明显参与空间（1 行修复已合入），可留意其是否应随 for-7.4-fixes 补 Cc: stable。

## 参考链接

- lore thread（Applied）: https://lore.kernel.org/all/d71ce22da31bceab849e0ca8dc39fe2b@kernel.org/
- lore thread（Tejun 对 bpf-next 版本的长篇解释）: https://lore.kernel.org/all/1ee462ef3e697e999011e4a0cd2864bd@kernel.org/
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20261107-007
date: '2026-11-07'
subject: "sched_ext: Reset task fields on exit of an SCX_TASK_READY task"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261106142818.1475-1-rahadbhuiya2021@gmail.com>"
lore_url: "https://lore.kernel.org/all/d71ce22da31bceab849e0ca8dc39fe2b@kernel.org/"
authors: [Rahad Bhuiya]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261106142818.1475-1-rahadbhuiya2021@gmail.com>"
    date: '2026-11-06'
    summary: "在 __scx_disable_and_exit_task 的 SCX_TASK_READY 分支补 scx_reset_task_fields()"
    review_outcome: "Tejun Heo 应用并回复 Applied to sched_ext/for-7.4-fixes"
upstream_commit: null
fixes_commit: "a298fd5f4ee8"
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "观察是否随 for-7.4-fixes 进入主线；评估是否补 Cc: stable"
contribution_opportunities: []
generated_at: "2026-11-08T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261106-015]
tags: [sched_ext]
---