# softirq: Treat an interrupted idle task as idle in tick_irq_exit()

## TL;DR

Radu Toader 的修复**今日合入 tip/sched/core**（commit `b251360cb2e6`，Committer Peter Zijlstra）：`tick_irq_exit()` 只在 `sched_core_idle_cpu()`（即 `idle_cpu()`）为真时跑 `tick_nohz_irq_exit()`，但 sched_ext 的 BPF 调度器把可运行任务扣在队列里（如 cgroup 限 CPU）时，`rq->nr_running` 非零、`idle_cpu()` 为假，导致 idle 循环里被中断后 sched_clock 不再被标记回 idle，不稳定的 sched_clock 时钟被钳位。修复把「被中断的 idle 任务」也视为 idle。

## 背景与问题

`tick_irq_exit()` 只在 `idle_cpu()` 为真时调用 `tick_nohz_irq_exit()`。但在 sched_ext 下，CPU 停在 idle 循环时其 BPF 调度器可能仍把一个 runnable 任务扣在自己的队列里（例如一个 cgroup 达到 CPU 限额的任务），该任务计入 `rq->nr_running`，使 `idle_cpu()` 为假。此时 idle 循环中的中断不会走 `tick_nohz_irq_exit()`，sched_clock 不会被重新标记为 idle（`TS_FLAG_IDLE_ACTIVE`、`sched_clock_idle_sleep_event()`）；在不稳定 sched_clock（如 kvm-clock 无稳定 TSC）下，tick-stopped idle 的时钟被钳位到「上一次 stamp + 一个 tick」，导致任务被 reschedule IPI 选走后时钟偏斜。

## 技术方案

让 `tick_irq_exit()` 在「当前任务是 idle 任务、只是被中断打断」时也视为 idle，从而正确执行 `tick_nohz_irq_exit()`，恢复 idle 时钟标记。属正确性修复。

## 版本演进与当前进展

已合入 tip/sched/core（`b251360cb2e6`，AuthorDate 2026-11-11，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（sched maintainer）**：作为 Committer 合入。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/core（`b251360cb2e6`）。*blocking_issues*：无。*next_action*：观察随 sched/core 进入下一 mainline 合入窗口。

## 效果评估

无量化数据；修复不稳定性 sched_clock 下 tick-stopped idle 的时钟钳位偏斜。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/b251360cb2e6c7b74d962831f5797a4520511b36
- lore thread: https://lore.kernel.org/lkml/20261106094343.174905-2-radu.m.toader@gmail.com/

---
id: sched-20261118-021
date: '2026-11-18'
subject: "softirq: Treat an interrupted idle task as idle in tick_irq_exit()"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261106094343.174905-2-radu.m.toader@gmail.com>"
lore_url: "https://lore.kernel.org/lkml/20261106094343.174905-2-radu.m.toader@gmail.com/"
authors: [Radu Toader]
maintainers_involved: [Peter Zijlstra]
current_version: v1
patch_series: []
upstream_commit: "b251360cb2e6c7b74d962831f5797a4520511b36"
fixes_commit: null
merged_branch: "tip/sched/core"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "观察随 sched/core 进入下一 mainline 合入窗口"
contribution_opportunities: []
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 1
related_articles: []
tags: [idle, nohz, sched_clock, sched_ext]
---
