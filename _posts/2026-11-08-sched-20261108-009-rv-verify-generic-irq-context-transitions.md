---
id: sched-20261108-009
date: '2026-11-08'
subject: 'rv: Verify generic IRQ context transitions'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <20261107171252.25090-1-kmehltretter@gmail.com>
lore_url: https://lore.kernel.org/all/20261107171252.25090-1-kmehltretter@gmail.com/
authors:
- Karl Mehltretter
maintainers_involved: []
current_version: v2
patch_series:
- version: v2
  msgid: <20261107171252.25090-1-kmehltretter@gmail.com>
  date: '2026-11-07'
  summary: 9 补丁：给 preempt_schedule_irq 加裸 tracepoint，新增 irqexit RV monitor 与 KUnit
    测试，验证 IRQ 退出调度归属
  review_outcome: RFC，无人表态
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - RFC v2 无人表态
  - 架构特定 interrupt-return 路径不在验证覆盖内
  next_action: 等待 rv/tracing 与 sched 侧对 tracepoint 与 monitor 设计表态
contribution_opportunities:
- kind: review
  description: 评估 preempt_schedule_irq 裸 tracepoint 对调度热路径/PREEMPT_RT 的开销与 owner 迁移可靠性
- kind: testing
  description: 在启用 CONFIG_RV 的平台跑 patch 7/9 的 KUnit 与 live 用例验证 monitor 守卫
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- preempt
title: 'rv: Verify generic IRQ context transitions'
layout: article
---

## TL;DR

Karl Mehltretter 的 RFC v2 系列（9 补丁）为 Runtime Verification（rv）框架新增「IRQ 退出时的调度归属」验证：在 `preempt_schedule_irq()` 前后加裸 tracepoint（不导出 tracefs），记录发起调度的 owner 任务，再用一个 per-task 的 hybrid-automaton 监控器跟踪该调用穿越挂起/迁移/恢复/返回的完整生命周期，并配 KUnit 测试。调度相关性在于 patch 2/9 直接给 `kernel/sched/core.c` 与 `include/trace/events/sched.h` 加 tracepoint。RFC，当日无人表态。

## 背景与问题

`preempt_schedule_irq()` 是 IRQ 返回路径上的通用调度入口：中断期间发生抢占时，发起调度的任务可能在调用返回前切换出去、甚至迁移到别的 CPU，现有 `__schedule()` 周围的 tracepoint 无法标识一次 `preempt_schedule_irq()` 调用的起止，也无法回答「这次 IRQ 退出时到底谁在调度、之后又轮到谁」。作者提出用 RV monitor 验证 IRQ context 转换的调度归属，先决条件是调度器里得有能跟踪 owner 的 tracepoint。

## 技术方案

- **patch 2/9 `tracing/sched: Add IRQ preemption lifecycle tracepoints`**：用 `DECLARE_TRACE()`（不导出 tracefs）在 `preempt_schedule_irq()` 通用 helper 前后加 `sched_irq_preempt_entry`/`sched_irq_preempt_exit` 两个裸 tracepoint，均把调用 `preempt_schedule_irq()` 的任务记为 owner，并在分发回调前采样 preempt count 与中断状态。`include/trace/events/sched.h` +26、`kernel/sched/core.c` +6。作者明确这两个 tracepoint 只括住 helper，不覆盖架构特定的 interrupt-return 工作。
- **patch 4/9 `rv: Add a monitor for IRQ-exit scheduling ownership`**：per-task 的 irqexit hybrid-automaton monitor（`kernel/trace/rv/monitors/irqexit/`），守卫 hardirq 上下文、本地中断状态与任务归属，跟踪一次调用从 entry 经 suspension/migration/resumption 到 return 的全过程；生成的模型头可由附带的 DOT 文件用未修改的 rvgen 工具复现。
- **patch 7/9 `rv: Add KUnit coverage for IRQ-exit scheduling`**：KUnit 测试生成状态表、非法迁移、启用期同步，并实测「无切换 / 跨任务切换 / 跨 CPU 迁移」三种 live `preempt_schedule_irq()` 调用（540 行 kunit 文件）。
- **patch 9/9**：测试 IRQ-exit softirq 的 hardirq→softirq→hardirq 序列与嵌套 hardirq。

## 版本演进与当前进展

*current_version: v2（RFC，2026-11-07 发出，msgid 20261107171252.25090-1）*。当日缓存仅见 3/9（patch 2/4/7）与 cover/9/9 主题，无评审。

## Maintainer 意见与讨论焦点

当日无维护者回帖。系列为 RFC、目标是「验证」而非改调度语义；可能的讨论点集中在：给 `preempt_schedule_irq()` 加 tracepoint 的开销、monitor 对架构特定 interrupt-return 工作的不覆盖（作者在 patch 2/4 的说明中反复声明这一边界）是否会限制验证价值。

## 合入评估

*likelihood=unknown*。RFC v2、无人表态，且主战场在 `kernel/trace/rv` 而非 `kernel/sched`（调度侧仅 patch 2/9 的 tracepoint），合入走向取决于 rv/tracing 维护者（Steven Rostedt 等）与调度侧对 tracepoint 开销的接受度。*blocking_issues*：① 无评审；② 架构特定 interrupt-return 路径不在验证覆盖内。*next_action*：等待 rv/tracing 与 sched 侧对 tracepoint 与 monitor 设计表态。

## 效果评估

无性能数据。tracepoint 用 `DECLARE_TRACE()`（非 tracefs 导出）意在压低开销，但无量化；验证价值是正确性保障而非性能。

## 我可以参与的点

- **review**：评估 `preempt_schedule_irq()` 裸 tracepoint 的加入是否会对调度热路径/`PREEMPT_RT` 行为带来可观测开销，以及 owner 记录在迁移场景下是否可靠。
- **testing**：在启用 `CONFIG_RV` 的平台跑 patch 7/9 的 KUnit 与 live 用例，验证 monitor 的守卫逻辑。

## 参考链接

- lore thread（cover）: https://lore.kernel.org/all/20261107171252.25090-1-kmehltretter@gmail.com/
- 相关补丁（tracepoint）: https://lore.kernel.org/all/20261107171252.25090-3-kmehltretter@gmail.com/
