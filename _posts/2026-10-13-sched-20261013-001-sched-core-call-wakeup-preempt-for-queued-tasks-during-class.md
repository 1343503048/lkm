---
id: sched-20261013-001
subject: 'sched/core: Call wakeup_preempt() for queued tasks during class change'
date: 2026-10-13
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: <8fa7f795-518c-4507-b684-60b0c1cac2c5@paulmck-laptop>
lore_url: https://lore.kernel.org/all/20261013152455.9039-1-kprateek.nayak@amd.com/
authors:
- K Prateek Nayak
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
current_version: v1
patch_series:
- version: v1
  msgid: <20261013152455.9039-1-kprateek.nayak@amd.com>
  date: 2026-10-13
  summary: 在 sched_change_end() 对 ctx->queued 情形调用 wakeup_preempt()，修 lost wakeup
  review_outcome: Peter 认可并要求落正式补丁；Vincent 提议 ctx->running→queued 改动，无异议
upstream_commit: null
fixes_commit: 1e900f415c60
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 维护者复审并合入 tip/sched/urgent
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 11
related_articles: []
tags:
- cfs
- preempt
title: 'sched/core: Call wakeup_preempt() for queued tasks during class change'
layout: article
---

> **subject**：sched/core: Call wakeup_preempt() for queued tasks during class change

## TL;DR
Paul E. McKenney 报告 rcutorture TREE01 场景下（x86 与 arm64）调度器「明显丢失唤醒」，CPU 带着可运行任务却陷入 idle、触发 RCU CPU stall。K Prateek Nayak 定位到 `sched_change_end()` 里对「已入队但非 current」任务改类（如 OTHER→RT）时既不升级 `rq->next_class` 也不 `resched_curr()`，导致 `sched_balance_newidle()` 看不到有更高优先级任务入队、直接选 idle。今日发出正式修复补丁（Peter 明确要求「把这堆分析变成 nice patch」）——对 `ctx->queued` 情形调用 `wakeup_preempt()` 重新评估 `rq->next_class`，已含测试数据，方向获 Peter/Vincent 认可。

## 背景与问题
触发命令 `kvm.sh --allcpus --duration 20m --configs '19*TREE01' --bootargs "nohz=off ..."`（每 8 个 CPU 分一个 17 vCPU 的 guest）跑 rcutorture TREE01，`rcu_torture_reader()` kthread 掉队引发 RCU stall。诊断补丁显示：stalled kthread 始终「在一个 idle CPU 上被抢占」，这一瞬时状态可持续数十秒。Prateek dump 该 CPU 的 rq 状态时发现：

- `rq->next_class = &fair_sched_class`
- `rq->nr_running = 1`
- `rq->cfs.h_nr_queued = 0`
- `rq->rt.rt_nr_running = 1`

即等待中的任务是 RT，但 `rq->next_class` 仍停留在低优先级的 fair 类。

根因是 `sched_change_end()` 与 `__sched_setscheduler()` 的竞态：CPU0 的 `pick_task_fair()` 在 `sched_balance_newidle()` 里临时 drop rq_lock，此窗口内 CPU1 把任务 enqueue 后又把它从 fair 升到 RT。升级走 `sched_change_end()`，但此时 `ctx->queued` 为真（`p->on_rq=1`）、`ctx->running` 为假（p 非 donor），于是 `resched_curr()` 与 `rq->next_class` 升级统统被跳过。新 idle 平衡抓回 rq_lock 后只看 `cfs.h_nr_queued`（已变 0）与 `rq_modified_above()`（`next_class` 仍是 fair），于是 `pick_task_fair()` 返回 NULL、CPU 选 idle，`nr_running=1` 却 `!need_resched()`。

`Fixes: 1e900f415c60 ("sched: Detect per-class runqueue changes")`。

## 技术方案
在 `sched_change_end()` 中，把「升级检测 + 唤醒抢占」的逻辑从 `ctx->running` 分支中拆出：新增 `if (ctx->queued) wakeup_preempt(rq, p, 0);`，让已入队（但未运行）的任务在改类后也重新评估 `rq->next_class` 并置 NEED_RESCHED。这样 newidle 平衡能通过 `rq_modified_above()` 看到「有更高优先级任务入队」而 RETRY_TASK、重新 pick，而非误选 idle。

讨论中锤炼出的共识（Peter/Vincent/Prateek 三角讨论）：
- `ctx->running` 的旧逻辑是为「current 任务仍是最优选择时避免多余 resched/wakeup_preempt」而优化，不应删。
- 简单版 Sampler 曾提议 `if (ctx->queued && sched_class_above(...)) { next_class=p->sched_class; resched_curr(); }`；Peter 建议对 queued 情形直接 `wakeup_preempt()`（天然覆盖「p 升到与 `rq->curr` 同类」的分支）；降级情形下不需要 `resched_curr()`（queued 任务本不在跑）。

改动仅 `kernel/sched/core.c`（+9/−10），base 为 tip:sched/urgent @ `a0bb6fac53fa`。

## 版本演进与当前进展
v1（今日首发，`<20261013152455.9039-1-kprateek.nayak@amd.com>`）。此前同线程里 Prateek 先给出过诊断 diff（`if (ctx->queued && sched_class_above(...)){next_class=...; resched_curr();}`），经 Peter 与 Vincent 多轮讨论（Vincent 提议把 `if (ctx->running)` 改成 `if (ctx->queued)`，Peter 补充分离 running/queued 两分支）+ Prateek 自己再次简化，最终定稿为 `if (ctx->queued) wakeup_preempt(rq, p, 0);`。今日尚无进一步 review。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（sched 维护者）：认可诊断，明确表态「Yes, that'll do. Can you turn all this into a nice patch -- you've done all the hard work on it anyway」，要求把分析落成正式补丁。
- **Vincent Guittot**（sched 维护者）：主动给出 `if (ctx->running) → if (ctx->queued)` 的修改示意，指出降级情形「not running 时无用」；后续又补充「我真正想指的就是 `sched_class_above(p->sched_class, ctx->class)` 这一分支」。
- 无明显 NAK；三方意见一致收敛到「queued 情形要唤醒抢占、running 情形保留既有优化」。

## 合入评估
*likelihood=high*。根因清晰、有复现、有 Fixes 标签、base tip:sched/urgent（意味着走紧急修复通道），Peter 已认可并点名要正式补丁。*blocking_issues*：正式补丁刚发，待 Peter/Vincent 复审收取。*next_action*：维护者 review 该 patch 并合入 tip/sched/urgent。

## 效果评估
补丁已在作者环境通过 `sched-messaging` 与 Paul 的 TREE01 reproducer（git 提交信息）；Prateek 贴出加 diff 后的 512 CPUs 机器上 `64*TREE01` 输出（各 TREE01.x 约 27.5–30.2 GP/s、exitcode 0、无 complaint）。此前诊断阶段 Prateek 明确「I haven't been able to hit the warnings with the below diff」。这些为复现通过类数据，未见对最终定稿（wakeup_preempt 版）的独立基准对比。

## 我可以参与的点
当前阶段暂无明显参与空间——根因已定位、正式修补已发、测试覆盖较全，可持续观察该补丁是否被 tip/sched/urgent 收取，以及是否触发 stable backport（该竞态涉及类升级路径，后续可能需要确认影响面与回合范围）。

## 参考链接
- lore thread（bug 报告根）：https://lore.kernel.org/all/8fa7f795-518c-4507-b684-60b0c1cac2c5@paulmck-laptop/
- 补丁 lore：https://lore.kernel.org/all/20261013152455.9039-1-kprateek.nayak@amd.com/
