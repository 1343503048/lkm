---
id: sched-20261008-005
subject: 'sched_ext: Fix stall when a task enqueued with SCX_ENQ_LAST lands back on
  its CPU''s local DSQ'
date: '2026-10-08'
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <2b405553751fe811b4cd2c24f307d961@kernel.org>
lore_url: https://lore.kernel.org/all/2b405553751fe811b4cd2c24f307d961@kernel.org/
authors:
- Tejun Heo
maintainers_involved:
- Tejun Heo
current_version: v1
patch_series:
- version: v1
  msgid: <2b405553751fe811b4cd2c24f307d961@kernel.org>
  date: '2026-10-08'
  summary: ENQ_LAST 任务落回本地 local DSQ 时在切进任务上置 need_resched
  review_outcome: 本日无回帖
upstream_commit: null
fixes_commit: f0e1a0643a59
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 进入 for-7.3-fixes 并随周期回合 stable
contribution_opportunities:
- kind: testing
  description: 用 ENQ_LAST 无 ENQ_EXITING 的调度器复现 mass cgroup teardown 并验证修复
- kind: review
  description: 确认 need_resched 覆盖三条 skip 路径
generated_at: '2026-10-09T01:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_ext
- hang
title: 'sched_ext: Fix stall when a task enqueued with SCX_ENQ_LAST lands back on
  its CPU''s local DSQ'
layout: article
---

## TL;DR

Tejun Heo 修掉 sched_ext 的一个 CPU idle stall：`SCX_OPS_ENQ_LAST` 下，本应作为「最后一个可运行任务」交给 `ops.enqueue()` 的任务，在三条 skip 路径（exiting 任务没设 `ENQ_EXITING`、migration-disabled 任务没设 `ENQ_MIGRATION_DISABLED`、offline rq 上的任务）会直达本 CPU 的 local DSQ，而 pick 已结算到 idle、没有任何东西再重新调度——CPU 挂着排队的任务空转，直到偶然的唤醒或 watchdog。scx_mitosis 在 mass cgroup teardown 时踩中：exiting 任务卡在 `exit_mmap()` 超过 40 秒。修复是在切进的任务上置 `need_resched`（仿 `proxy_resched_idle()`）。带 `Fixes:` + `Cc: stable # v6.12+`。

## 背景与问题

`SCX_OPS_ENQ_LAST` 语义是「CPU 上最后一个可运行任务不 keep，改交给 `ops.enqueue()` 决定去向」。但有三类任务会跳过 `ops.enqueue()`、被直接放进本 CPU 的 local DSQ：没有 `SCX_OPS_ENQ_EXITING` 的 exiting 任务、没有 `SCX_OPS_ENQ_MIGRATION_DISABLED` 的 migration-disabled 任务、offline rq 上的任务。这一放发生在 `put_prev_task_scx()` 中、pick 已确定为 idle 之后，因此没有后续调度事件去消费这个任务，CPU 便带着排队的任务 idle，直到无关唤醒落到该 CPU 或 watchdog 触发。scx_mitosis（设了 `ENQ_LAST` 但没设 `ENQ_EXITING`）在大量 cgroup teardown 时命中：exiting 任务卡在 `exit_mmap()` 超过 40 秒。

## 技术方案

若 `SCX_ENQ_LAST` 的 enqueue 最终把这个任务留在了本 CPU 的 local DSQ，就在「正在被切进来的任务」上置 `need_resched`，与 `proxy_resched_idle()` 的做法一致。之所以不能简单用 `resched_curr()`：那会标记「正在被切出去的任务」，而 `__schedule()` 恰好在 pick 之后立刻清掉该标记，等于无效。

## 版本演进与当前进展

单枚修复初次发出（`<2b405553751fe811b4cd2c24f307d961@kernel.org>`），目标分支 `sched_ext/for-7.3-fixes`，带 `Reported-by: Xiangyu Bu <xbu@meta.com>` 与复现 PR 链接（`sched-ext/scx#3870`）。当日无回帖。

## Maintainer 意见与讨论焦点

作者即 sched_ext 维护者 Tejun Heo，本日为 self-authored fix 首发，无他人回帖。无争议点；修复思路复用既有 `proxy_resched_idle()` 范式，逻辑自洽。

## 合入评估

*likelihood=high*。维护者自己的 liveness 修复、定向 `for-7.3-fixes`、带明确 `Fixes: f0e1a0643a59`（sched_ext 初始实现）、`Cc: stable # v6.12+`、有真实上报者与复现 PR。*blocking_issues*：暂无；仅等合入确认。*next_action*：进入 sched_ext/for-7.3-fixes 并随 7.3/7.4 周期回合 stable。

## 效果评估

作者描述症状明确：mass cgroup teardown 下 exiting 任务卡 `exit_mmap()` 超过 40 秒（非纯理论，来自 `Reported-by` 的真实场景）。修复本身是 liveness 变更、无性能数据。

## 我可以参与的点

- `testing`：用设了 `ENQ_LAST` 而没设 `ENQ_EXITING`/`ENQ_MIGRATION_DISABLED` 的调度器（如 scx_mitosis）复现 mass cgroup teardown，验证修复后不再 stall。
- `review`：确认 `need_resched` 的落点在三条 skip 路径（exiting / migration-disabled / offline rq）上都覆盖到了。

## 参考链接

- 补丁: https://lore.kernel.org/all/2b405553751fe811b4cd2c24f307d961@kernel.org/
