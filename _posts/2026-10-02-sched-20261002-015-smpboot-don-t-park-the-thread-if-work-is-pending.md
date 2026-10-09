---
id: sched-20261002-015
date: '2026-10-02'
subject: 'smpboot: Don''t park the thread if work is pending'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260911143815.997254-1-bigeasy@linutronix.de>
lore_url: https://lore.kernel.org/all/20260911143815.997254-4-bigeasy@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20260911143815.997254-1-bigeasy@linutronix.de>
  date: '2026-09-11'
  summary: 4 补丁：irq_work 注释更新、RT lazy flush、smpboot park 顺序修复
  review_outcome: '10-02 三片（2-4/4）合入 tip: sched/core'
upstream_commit: 4a3b51aab6e25244d97936aa65e6d5425adf98e1
fixes_commit: null
merged_branch: tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪系列 1/4 是否随后合入
contribution_opportunities:
- kind: testing
  description: PREEMPT_RT 上 CPU offline/online+printk 验证 lazy irq_work 不再卡死
- kind: review
  description: 后验 irq_work_run_cpu() 远程代跑对非 LAZY 用户的边界
generated_at: '2026-10-03T01:00:00'
source_email_count: 3
related_articles: []
tags:
- hotplug
- rt
title: 'smpboot: Don''t park the thread if work is pending'
layout: article
---

> **subject**：`smpboot: Don't park the thread if work is pending`

## TL;DR

Sebastian Andrzej Siewior（linutronix，PREEMPT_RT 维护者）4 补丁系列（09-11 发出，`<20260911143815.997254-...>`，系列 1/4 未随本轮合入）中的 2/4-4/4 三片于 10-02 由 Peter Zijlstra 合入 tip: sched/core（CommitterDate 10-01）：4/4 `smpboot: Don't park the thread if work is pending`（4a3b51aab6e2）——CPU 热插拔 park 请求到达时 smpboot 线程可能已接到 work 但尚未运行，原逻辑直接 park 导致回调卡死到 CPU 重新 online；改为有待跑 work 时先执行回调、下一轮再 park。3/4 `irq_work: Flush lazy work CPU down on PREEMPT_RT`（40dcc9bdbef3）——RT 上 lazy_list 的 irq_work 需要 thread context、CPU 下线时没人 flush，single 型 irq_work 卡在 "claimed" 状态无法复用（症状：CPU down 路径的 late printk 不再输出），新增 `irq_work_run_cpu()` 由控制 CPU 在 `smpcfd_dead_cpu()` 里代跑。2/4 `irq_work: Update a comment regarding CPU hotplug invocation`（791b1760accd）注释更新。系列未在既往分析窗口覆盖。

## 背景与问题

两处 CPU 热插拔与 per-CPU 线程/工作的边界缺陷：

1. **smpboot 线程 park 吞掉已排入的 work**：smpboot 线程（如 migration/stopper 类 hotplug 线程）接到 work 时被唤醒；若它尚未得到运行机会就收到 CPU-hotplug park 请求，原 `smpboot_thread_fn()` 的 `if (kthread_should_park())` 分支直接 park——**回调没有执行**，排入的 work 卡死直到该 CPU 重新 online。
2. **PREEMPT_RT 上 lazy irq_work 在 CPU 下线时无人 flush**：RT 把 IRQ_WORK_LAZY 及非 HARD_IRQ 标记的回调放到 thread context 执行；CPU 下线时 `smpcfd_dying_cpu()`（目标 CPU、关中断）flush 的只有非 lazy 部分。lazy_list 上的回调留存、等 CPU 回来才被处理。per-CPU irq_work 本地 enqueue 仍正常，但 offline CPU 上的条目卡住；**single 型 irq_work 更糟**——保持 "claimed" 状态不能复用。可见症状：CPU down 路径的 late printk enqueue 了打印 irq_work 却永不调度、后续 printk 因其 pending 不再上控制台；等待其完成的 cancel/flush 任务会一直阻塞。

## 技术方案

- **4/4（kernel/smpboot.c +4/−2）**：`smpboot_thread_fn()` 里把 `should_run = td->status == HP_THREAD_ACTIVE && ht->thread_should_run(td->cpu)` 提前算好；park 判断改为 `if (kthread_should_park() && !should_run)`——有待跑回调时先跑完本轮（thread function 先执行、下一轮迭代再 park），确保 shutdown 前回调被处理。循环体后面复用同一 `should_run`。
- **3/4（3 文件 +14）**：新增 `irq_work_run_cpu(unsigned int cpu)`，在 `smpcfd_dead_cpu()`（控制 CPU、开中断、目标 CPU 已 shutdown 后立即调用）里代跑指定 dead CPU 的回调——llist 此时可安全访问。遍历 irq_work 用户后结论：回调在哪台 CPU 上跑无关紧要，远程代跑可行。
- **2/4**：更新 `irq_work` 关于 CPU hotplug 调用时机的注释（提及 commit 31487f8328f20 "smp/cfd: Convert core..." 的 hotplug 重构背景）。

## 版本演进与当前进展

- 系列 v1（09-11，4 补丁，`<20260911143815.997254-{1..4}-bigeasy@linutronix.de>`）：2/4-4/4 于 10-02 进 tip（Peter 合入，CommitterDate 2026-10-01 14:00:35-36）；1/4（本系列首片，主题不在当日缓存）未见合入回帖。
- 无评审争议记录（9 月窗口未覆盖该系列；合入即结论）。

## Maintainer 意见与讨论焦点

Peter Zijlstra 直接收取三片（Signed-off-by 链：Sebastian → Peter）。无未决分歧。3/4 的「远程代跑」设计（回调不挑 CPU）是唯一值得注意的语义放宽——Sebastian 自查过全部 irq_work 用户后确认无影响。

## 合入评估

*likelihood=merged*。已合入 tip: sched/core（commit 4a3b51aab6e2 / 40dcc9bdbef3 / 791b1760accd）。*blocking_issues*：无。*next_action*：跟踪 1/4 是否随后合入；PREEMPT_RT 场景的 CPU down printk 恢复可在 -rt 树验证。

## 效果评估

无 benchmark；属正确性修复。3/4 的症状链（CPU down 后 late printk 静默、cancel/flush 永久阻塞）在 commit message 中有完整机制描述，未见独立复现数据。

## 我可以参与的点

- `testing`：PREEMPT_RT 内核上反复 CPU offline/online + 并发 printk，验证 lazy irq_work 不再卡死（症状消失即回归测试）。
- `review`：核对 `irq_work_run_cpu()` 的远程代跑对 `IRQ_WORK_LAZY` 之外用户（如 arch 特定 raise 路径）的边界——合入快、覆盖面值得后验。

## 参考链接

- tip: smpboot park: https://git.kernel.org/tip/4a3b51aab6e25244d97936aa65e6d5425adf98e1
- tip: irq_work flush: https://git.kernel.org/tip/40dcc9bdbef3d93a516c8ee32cb1b50eddeeebcc
- tip: irq_work comment: https://git.kernel.org/tip/791b1760accdc15248929f9b767410a76be199b1
- 系列原帖（4/4）: https://lore.kernel.org/all/20260911143815.997254-4-bigeasy@linutronix.de/
