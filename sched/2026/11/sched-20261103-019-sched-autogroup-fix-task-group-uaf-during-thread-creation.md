# sched/autogroup: Fix task_group UAF during thread creation

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261023-004：Daehyeon Ko 修 autogroup UAF（`sched_cgroup_fork()` 在 CLONE_THREAD 子进程发布前指向旧 `autogroup->tg`，与 `ksys_setsid()` 竞态）。
- sched-20261026-003：Peter 质疑 NULL deref，建议把复杂度移到 `ksys_setsid()`。
- sched-20261030-008：Daehyeon 论证无 NULL deref、单挪 tasklist_lock 不关窗；Peter 收回否定、提议 `autogroup_move_group()` 也持 `cgroup_threadgroup_rwsem`。
- sched-20261031-012：Tejun 介入——`cgroup_threadgroup_rwsem` 是全局 percpu rwsem、常写持很贵；建议把 autogroup 赋值挪到 fork 更晚的位置。
- sched-20261102-020：Peter 回应 Tejun——为 autogroup 引入与 cgroup 不同的 `sched_task_group` 规则没吸引力。
- sched-20261103-019（今天）：Tejun 给出「移入 cpu controller 的 `cpu_cgroup_fork()`」的具体补丁；Peter 更进一步提议用 `sched_post_fork()`（新增 `autogroup_post_fork()`），只要保证在 `scx_post_fork()` 之前即可——方案向 sched 侧收敛。

## 背景与问题

（承接 sched-20261102-020）竞态时序不变：`sched_cgroup_fork()` 在任务发布（publishing）前就赋值 autogroup，导致 `ksys_setsid()` 可能错过新任务。今日焦点是把赋值挪到「发布之后」。

## 技术方案

（承接）今日出现两版方案代码：Tejun 提议把 autogroup 处理移入 cpu controller——`sched_cgroup_fork()` 只按 cgroup 放置任务，cpu controller 在任务上到 thread list 后应用 autogroup（新增 `cpu_cgroup_fork()`，在 `cpu_cgrp_subsys` 里挂 `.fork`）。Peter 回应：与其用 `cgroup_post_fork()`（不确定是否对所有 controller 都调 `.fork`），不如直接挪进 `sched_post_fork()`，新增 `autogroup_post_fork()`——`if (READ_ONCE(sysctl_sched_autogroup_enabled) && task_wants_autogroup(p, p->sched_task_group)) sched_move_task(p, true);`——只需确保发生在 `scx_post_fork()` 之前，并附了补丁草图。

## 版本演进与当前进展

*current_version: v1（原补丁未更新）*。今日方案走向进一步从「cgroup 侧」移到「sched 侧」。

## Maintainer 意见与讨论焦点

Tejun：不想在每个 `setsid()` 上取写锁，宁可晚赋值，倾向把 autogroup 放进 cpu controller，「这不是我要死磕的山头，但看起来方向更好」。Peter：认可「不在 `sched_cgroup_fork()` 而在发布后赋值」的方向，但认为 `cgroup_post_fork()` 别扭，改为 `sched_post_fork()` 更自然。双方收敛到同一目标（发布后赋值），仅实现落点（cpu controller vs sched_post_fork）有差异。

## 合入评估

*likelihood=low*。方案仍在多个维护者之间收敛，原补丁作者（Daehyeon）需落地最终实现（大概率是 Peter 的 `sched_post_fork()` 路线）。*next_action*：作者按 `autogroup_post_fork()` 方案出 v2，并确认在 `scx_post_fork()` 之前执行。

## 效果评估

（承接）UAF 修复本身无性能数据。

## 我可以参与的点

- review：评估 `autogroup_post_fork()` 放在 `sched_post_fork()` 后是否真能消除与 setsid 的竞态，及与 `scx_post_fork()` 的顺序约束。
- new_patch：按 Peter 草图把原补丁改成 `sched_post_fork()` 路线出 v2。

## 参考链接

- lore thread（今日 Peter 回帖）: https://lore.kernel.org/all/20261103114557.GJ1813469@noisy.programming.kicks-ass.net/

---
id: sched-20261103-019
date: 2026-11-03
subject: "sched/autogroup: Fix task_group UAF during thread creation"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: null
lore_url: "https://lore.kernel.org/all/20261103114557.GJ1813469@noisy.programming.kicks-ass.net/"
authors: [Daehyeon Ko]
maintainers_involved: [Peter Zijlstra, Tejun Heo]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues: ["方案落点（cpu controller vs sched_post_fork）未最终确定"]
  next_action: "按 autogroup_post_fork() 方案出 v2，确认在 scx_post_fork 之前执行。"
contribution_opportunities:
  - kind: review
    description: "评估 sched_post_fork 路线是否消除与 setsid 的竞态。"
  - kind: new_patch
    description: "按 Peter 草图改 sched_post_fork 路线出 v2。"
generated_at: "2026-11-04T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261102-020]
tags: [autogroup]
---