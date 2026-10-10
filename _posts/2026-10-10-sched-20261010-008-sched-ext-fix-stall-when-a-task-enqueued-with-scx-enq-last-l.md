---
id: sched-20261010-008
date: '2026-10-10'
subject: 'sched_ext: Fix stall when a task enqueued with SCX_ENQ_LAST lands back on
  its CPU''s local DSQ'
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
  review_outcome: Applied 到 sched_ext/for-7.3-fixes
upstream_commit: null
fixes_commit: f0e1a0643a59
merged_branch: sched_ext/for-7.3-fixes
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 随 for-7.3-fixes pull 进主线并回合 stable v6.12+
contribution_opportunities:
- kind: testing
  description: 用 ENQ_LAST 无 ENQ_EXITING 调度器复现 mass cgroup teardown 验证不再 stall
generated_at: '2026-10-11T09:00:00'
source_email_count: 1
related_articles:
- sched-20261008-005
tags:
- sched_ext
- hang
title: 'sched_ext: Fix stall when a task enqueued with SCX_ENQ_LAST lands back on
  its CPU''s local DSQ'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-005-sched-ext-fix-stall-when-a-task-enqueued-with-scx-enq-last-l.html">sched-20261008-005</a>：Tejun Heo 修掉 sched_ext 的 CPU idle stall——`SCX_OPS_ENQ_LAST` 下本应交给 `ops.enqueue()` 的「最后一个可运行任务」在三条 skip 路径（exiting 未设 `ENQ_EXITING`、migration-disabled 未设 `ENQ_MIGRATION_DISABLED`、offline rq）会直达本地 DSQ，而 pick 已结算到 idle、没有任何东西再重新调度。修复是在切进任务上置 `need_resched`（仿 `proxy_resched_idle()`），带 `Fixes:` + `Cc: stable v6.12+`。
- <a class="article-ref" href="/lkm/2026/10/10/sched-20261010-008-sched-ext-fix-stall-when-a-task-enqueued-with-scx-enq-last-l.html">sched-20261010-008</a>（今天）：**Tejun 回帖「Applied to sched_ext/for-7.3-fixes」**，该 liveness 修复进入维护者 fixes 分支，随 7.3-rc 周期回合。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/08/sched-20261008-005-sched-ext-fix-stall-when-a-task-enqueued-with-scx-enq-last-l.html">sched-20261008-005</a>）`SCX_ENQ_LAST` 语义下，本应由 `ops.enqueue()` 作为「最后一个可运行任务」处理的任务，在三条 skip 路径会绕过 BPF 直达本地 DSQ，而 pick 已经结算到 idle、没有任何机制再触发重调度——CPU 挂着排队的任务空转，直到偶然唤醒或 watchdog。scx_mitosis 在 mass cgroup teardown 时踩中：exiting 任务卡在 `exit_mmap()` 超过 40 秒。今天无新的技术内容，是合入进展更新。

## 技术方案
（承接）修复是在切进的任务上置 `need_resched`，复用既有 `proxy_resched_idle()` 范式，覆盖三条 skip 路径的 liveness 缺口。今天无代码变化。

## 版本演进与当前进展
- v1（10-08，`<2b405553751fe811b4cd2c24f307d961@kernel.org>`，见 related_articles）。
- 今天（Tejun 回帖 `<85e1c03116c07e0192a982674199d815@kernel.org>`）：「Applied to sched_ext/for-7.3-fixes. Thanks.」——进入维护者 fixes 分支。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（维护者+作者）：今天确认 applied 到 sched_ext/for-7.3-fixes。无争议、无他人回帖。

## 合入评估
*likelihood=high*。维护者自己的 liveness 修复已 applied 到 `sched_ext/for-7.3-fixes`，带 `Fixes: f0e1a0643a59`、`Cc: stable v6.12+`、真实上报者与复现 PR（scx#3870）。*blocking_issues*：无（待 pull）。*next_action*：随 sched_ext for-7.3-fixes pull 进主线并回合 stable v6.12+。

## 效果评估
此前报告的复现为 mass cgroup teardown 下 exiting 任务卡 `exit_mmap()` 超 40 秒（见 related_articles）；今天无新增数据，仅合入进展。

## 我可以参与的点
- 用「ENQ_LAST + 无 ENQ_EXITING」的调度器复现 mass cgroup teardown，验证 applied 版本后不再 stall；
- 跟踪 stable v6.12+ 的回合。

## 参考链接
- patch: https://lore.kernel.org/all/2b405553751fe811b4cd2c24f307d961@kernel.org/
- Tejun applied: https://lore.kernel.org/all/85e1c03116c07e0192a982674199d815@kernel.org/
