# sched/core: Call wakeup_preempt() for queued tasks during class change

> **subject**：sched/core: Call wakeup_preempt() for queued tasks during class change

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261013-001：Paul E. McKenney 报告 rcutorture TREE01 下调度器「lost wakeup」（CPU 带着可运行 RT 任务却 idle、触发 RCU stall）；K Prateek Nayak 定位到 `sched_change_end()` 对「已入队但非 current」任务改类时不升级 `rq->next_class` 也不 `resched_curr()`，当日发出修复补丁。
- sched-20261014-001（今天）：**该补丁已合入 tip/sched/urgent**，Commit-ID `118a2cf4ced60777a2408001e2b4838fed1cea55`。Peter「W00t, ok, let me go queue this stuff!」，整串 Review/Tested 标签（Vincent、Phil Auld、Paul McKenney 99.9% 置信度）齐备，当天收取。

## 背景与问题
（承接 20261013-001）rcutorture TREE01 场景（`nohz=off`、17 vCPU guest/8 CPU）下 `rcu_torture_reader()` kthread 掉队引发 RCU stall。Prateek dump 出 stall CPU 的 rq 状态：`rq->next_class = &fair_sched_class`、`nr_running = 1`、`cfs.h_nr_queued = 0`、`rt.rt_nr_running = 1`——等待任务是 RT，但 `next_class` 停留在 fair。根因是 `sched_change_end()` 与 `__sched_setscheduler()` 的竞态：`sched_balance_newidle()` 临时 drop rq_lock 的窗口内，任务被 enqueue 后又从 fair 升到 RT，此时 `ctx->queued` 为真、`ctx->running` 为假，升级 `next_class` 与 `resched_curr()` 全被跳过，newidle 平衡误选 idle。

今日修正因集经 Prateek 纠偏：正确 `Fixes:` 为 `704069649b5b ("sched/core: Rework sched_class::wakeup_preempt() and rq_modified_*()")`（此前二稿写的是 `1e900f415c60`，Prateek 说明该 commit 之前靠 `queue_mask` 在 enqueue 时捕获类变更，`704069649b5b` 才改成走 `next_class`/`wakeup_preempt()` 路径，因而才是引入点）。

## 技术方案
（承接 20261013-001）在 `sched_change_end()` 中把「升级检测 + 唤醒抢占」从 `ctx->running` 分支拆出：新增 `if (ctx->queued) wakeup_preempt(rq, p, 0);`，让已入队（未运行）任务在改类后重新评估 `rq->next_class` 并置 NEED_RESCHED，使 newidle 平衡能经 `rq_modified_above()` 看到更高优先级任务入队而 RETRY_TASK。tip 版实际改动 `kernel/sched/core.c`（+9/−10）：注释说明「switch*_from/to 各方都不知道新旧类，必须在改类处 resched」。降级情形仍需 `if (ctx->running)` 里原有 `resched_curr()`。

## 版本演进与当前进展
v1（10-13）→ **今日合入 tip/sched/urgent**。diff 演进很小：诊断版 `if (ctx->queued && sched_class_above(...)){next_class=...; resched_curr();}` 经 Peter/Vincent 三角讨论收敛为 `if (ctx->queued) wakeup_preempt(rq, p, 0);`。今日 Peter 回帖「W00t, ok, let me go queue this stuff!」并当天由 tip-bot2 合入，无 v2。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（committer）：认收并排队，最终提交。
- **Vincent Guittot**：`Reviewed-by`。
- **Phil Auld**：`Reviewed-by`，评价「rq lock dropping in schedule() 造成的意外还真是不少，这版也让代码更干净」。
- **Paul E. McKenney**（报告者）：`Tested-by`，统计上「99.9% 置信、bug 率下降超过两个数量级」。
- 无 NAK；Fixes 标签经 Prateek 与实践复核后落实为 `704069649b5b`。

## 合入评估
*likelihood=merged*。已进 tip/sched/urgent（commit `118a2cf4ced60777a2408001e2b4838fed1cea55`），`Fixes:` + `Reported-by`/`Tested-by`/多个 `Reviewed-by` 齐全，经 rcutorture TREE01 复现闭环。*blocking_issues*：无（已合入）；后续关注是否需 `Cc: stable` 回合。

## 效果评估
Prateek 在 512 CPUs 机器 `64*TREE01` 加 diff 后各 TREE01.x 约 27.5–30.2 GP/s、exitcode 0、无 complaint；Paul 的 TREE01 reproducer 亦通过（commit message 记录 Tested-by）。Paul 给出「99.9% 置信、bug 率下降 >2 个数量级」的量化表述，属复现通过类数据。

## 我可以参与的点
主线修复已合入，当前阶段暂无明显参与空间。可跟进是否有 stable backport 需求（该竞态涉及类升级路径，需确认影响面与回合范围），若维护者未主动 `Cc: stable`，可评估并提议。

## 参考链接
- tip commit：https://git.kernel.org/tip/118a2cf4ced60777a2408001e2b4838fed1cea55
- 补丁 lore：https://lore.kernel.org/all/20261013152455.9039-1-kprateek.nayak@amd.com/
- bug 报告根：https://lore.kernel.org/all/8fa7f795-518c-4507-b684-60b0c1cac2c5@paulmck-laptop/

---
id: sched-20261014-001
subject: 'sched/core: Call wakeup_preempt() for queued tasks during class change'
date: 2026-10-14
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: '<8fa7f795-518c-4507-b684-60b0c1cac2c5@paulmck-laptop>'
lore_url: 'https://lore.kernel.org/all/20261013152455.9039-1-kprateek.nayak@amd.com/'
authors:
  - 'K Prateek Nayak'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Vincent Guittot'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261013152455.9039-1-kprateek.nayak@amd.com>'
    date: 2026-10-13
    summary: 'sched_change_end() 对 ctx->queued 情形调用 wakeup_preempt()，修 lost wakeup'
    review_outcome: '当日合入 tip/sched/urgent（118a2cf4ced6），Review/Tested 标签齐全'
upstream_commit: '118a2cf4ced60777a2408001e2b4838fed1cea55'
fixes_commit: '704069649b5b'
merged_branch: 'tip/sched/urgent'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '已合入 tip/sched/urgent；跟进 stable backport 评估'
contribution_opportunities: []
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 9
related_articles:
  - sched-20261013-001
tags: [cfs, preempt]
---