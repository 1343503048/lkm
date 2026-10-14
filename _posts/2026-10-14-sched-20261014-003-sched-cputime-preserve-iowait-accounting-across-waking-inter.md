---
id: sched-20261014-003
subject: 'sched/cputime: Preserve iowait accounting across waking interrupts in dyntick-idle'
date: 2026-10-14
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261014015258.13967-1-wegao@suse.com>
lore_url: https://lore.kernel.org/all/20261014015258.13967-1-wegao@suse.com/
authors:
- Wei Gao
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261014015258.13967-1-wegao@suse.com>
  date: 2026-10-14
  summary: kcpustat_irq_enter() 检查 nr_iowait_cpu() 提前结算 iowait
  review_outcome: Peter 否决 nr_iowait_cpu 方案；Christian Loehle 分析并派生 accessor 重构补丁
upstream_commit: null
fixes_commit: 7198e3927a14
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 对 nr_iowait_cpu() 方案明确 NAK
  next_action: 换不依赖聚合 nr_iowait 的精确记账方案后再提
contribution_opportunities:
- kind: discussion
  description: 设计不依赖聚合 nr_iowait 的 per-CPU iowait idle 记账方案
- kind: review
  description: 评估 cpu_has_iowait 重构与本修复路径的关系
generated_at: '2026-10-15T01:00:00+08:00'
source_email_count: 4
related_articles: []
tags:
- nohz
- idle
title: 'sched/cputime: Preserve iowait accounting across waking interrupts in dyntick-idle'
layout: article
---

> **subject**：sched/cputime: Preserve iowait accounting across waking interrupts in dyntick-idle

## TL;DR
Wei Gao（SUSE）修复 liburing `test/iowait.t` 在 tickless + 无 IRQ time accounting 配置下间歇性失败的问题：任务在中断处理函数里被唤醒时，`rq->nr_iowait` 在 CPU 退出 idle 前已减到 0，导致整段 iowait 被记成 CPUTIME_IDLE。作者方案是在 `kcpustat_irq_enter()` 里检查 `nr_iowait_cpu()` 提前结算 iowait。Peter Zijlstra 当日否决——「用 `nr_iowait_cpu()` 本质上永远不是修复，是掷骰子」，该方案合入可能性低，需另寻更精确的记账路径。

## 背景与问题
`test/iowait.t` 在空 pipe 上提交 read、调 `io_uring_wait_cqe_timeout()` 设 1 秒超时：`current->in_iowait` 使 `rq->nr_iowait` 增到 1，CPU 进入 tickless idle 且停掉周期 tick。1 秒超时的 hrtimer 中断到来自 `io_cqring_timer_wakeup()` 调 `wake_up_process()`，`ttwu_do_activate()` 在 CPU 退出 idle 前把 `rq->nr_iowait` 减到 0。CPU 返回中断、`tick_nohz_idle_exit() → kcpustat_idle_stop()` 结算时因 `nr_iowait_cpu() > 0` 为假，把整 1 秒 iowait 记成了 CPUTIME_IDLE，导致 `diff < 50` 断言失败。

根因是 commit `7198e3927a14 ("sched/cputime: Handle idle irqtime gracefully")` 为优化在 IRQ time accounting 关闭时不再于 IRQ 进入处暂停 idle 记账，但未覆盖「任务在 IRQ 处理函数内被唤醒」这一窗口。`Fixes: 7198e3927a14`。

## 技术方案
作者在 `kcpustat_irq_enter()` 的条件里追加 `|| nr_iowait_cpu(smp_processor_id()) > 0`：CPU 处于 iowait 时在中断处理函数运行前先暂停并结算到 CPUTIME_IOWAIT；`kcpustat_irq_exit()` 相应在「因 iowait 暂停」时用 `!kc->idle_elapse` 恢复 tickless 记账（`kernel/sched/cputime.c` +7/−2）。

**Peter 当即否决**：`nr_iowait_cpu()` 是聚合的、可被本 CPU 上任意任务污染的计数，用它判断「本 CPU 此刻是否在 iowait」是掷骰子（该函数自带的注释正是警告此误用）。因此本补丁的方案不是可接受的修复。

## 版本演进与当前进展
v1（今日首发，`<20261014015258.13967-1-wegao@suse.com>`）。当日 Peter 否决方案、Christian Loehle 追加两封技术分析，无 v2。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（sched 维护者）：明确否决——「Using nr_iowait_cpu() is fundamentally never a fix. It is rolling a dice and liking random numbers.」（引用该函数注释）。这是对方案本身的 NAK，而非细节意见。
- **Christian Loehle**：指出该函数注释已过时（menu governor 不再用该 heuristic）、剩余聚合用户主要是记账/上报；`nr_iowait_cpu()`（vs `cpu_has_iowait()`）可被重构，并表示「我来发一个补丁」（衍生出同日的 `sched: Replace nr_iowait_cpu() with a bool accessor` 系列）。他还分析 test 的断言边界：a) in_iowait=0 时允许最多 +10 单位、b) in_iowait=1 时要求 ≥+50 单位，认为靠 CPU 聚合量验证 per-task `in_iowait` 本身就不太可行。

## 合入评估
*likelihood=low*。问题真实、有复现与 `Fixes:`，但 Peter 对 `nr_iowait_cpu()` 方案给出明确 NAK，当前补丁无法以现有形态合入。*blocking_issues*：方案被否，需换不依赖聚合 `nr_iowait` 的记账路径。*next_action*：作者需改走更精确的机制（如跟踪「进入 idle 时是否 in_iowait」的 per-CPU 原位状态，而非事后查聚合计数），再与 Peter 对齐。

## 效果评估
作者以 liburing `test/iowait.t` 复现（`iowait diff too small: 48`），未给量化收益数据；补丁目的为使该测试在目标配置下稳定通过。Peter 的反对是机制性的，与数据多寡无关。

## 我可以参与的点
- discussion：帮助作者设计「不依赖 `nr_iowait_cpu()` 聚合量」的 iowait 进入/退出 idle 记账方案——关键难点是 `in_iowait` 是 per-task 状态，与 CPU 级 idle 结算之间缺少一一对应。
- review：评估 Christian 的 `nr_iowait_cpu() → cpu_has_iowait()` 重构（见 <a class="article-ref" href="/lkm/2026/10/14/sched-20261014-004-sched-replace-nr-iowait-cpu-with-a-bool-accessor.html">sched-20261014-004</a>）是否能为「零/非零判定」类调用点提供更清晰的语义，以及它与此修复的关系。

## 参考链接
- 补丁 lore：https://lore.kernel.org/all/20261014015258.13967-1-wegao@suse.com/
- Peter 否决回帖：https://lore.kernel.org/all/20261014124934.GE4121339@noisy.programming.kicks-ass.net/
