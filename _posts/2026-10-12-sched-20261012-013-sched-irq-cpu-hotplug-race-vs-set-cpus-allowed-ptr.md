---
id: sched-20261012-013
date: '2026-10-12'
subject: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261012103946.aOSAmrRe@linutronix.de>
lore_url: https://lore.kernel.org/all/20261012103946.aOSAmrRe@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved:
- Peter Zijlstra
- Juri Lelli
current_version: v2
patch_series:
- version: v1
  msgid: <20260907085825.f-CZ1Q5y@linutronix.de>
  date: '2026-09-07'
  summary: RFC：CPU 热插拔与 set_cpus_allowed_ptr 竞态，两种修复示意
  review_outcome: sashiko 质疑 cpus_read_lock 死锁与 set_cpus_allowed_dl 绕过
- version: v2
  msgid: <20261012103946.aOSAmrRe@linutronix.de>
  date: '2026-10-12'
  summary: Repost 并收集意见，实现两个选项（cpus_read_lock / cpumask_set_cpu fallback）
  review_outcome: Juri 倾向 option1；Peter 质疑「irq 为何特殊」并要求完整故障图
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 质疑修复为何特化到 irq 路径、需完整故障场景与 TLA+ 模型扩展
  - option1/option2 尚未选定
  next_action: 作者回应 Peter 的「为何 irq 特殊」并提供完整竞态图，与 Juri 收敛到 option1
contribution_opportunities:
- kind: discussion
  description: 厘清该竞态是否同样影响其他 set_cpus_allowed_ptr 调用方（Peter 之问）
- kind: review
  description: 评估 option2 里 cpumask_set_cpu 绕过 set_cpus_allowed_dl 对 SCHED_DEADLINE
    不变量（p->nr_cpus_allowed）的影响
generated_at: '2026-10-13T01:40:00'
source_email_count: 3
related_articles:
- sched-20261003-008
tags:
- affinity
- rt
title: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-008-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20261003-008</a>（及 20260907-002）：Sebastian Siewior 的 RFC——syzbot 报出的 CPU 热插拔与 `set_cpus_allowed_ptr()` 竞态：IRQ 线程迁移到「当时在线但可能马上掉线」的 CPU，`__migrate_task()` 被 `is_cpu_allowed()` 拒后返回当前 rq，任务所在 CPU 与 `cpus_mask` 不再匹配。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-013-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20261012-013</a>（今天）：作者发 v2（两种修复示意：option1 在 `irq_thread_check_affinity()` 里 `scoped_guard(cpus_read_lock)`；option2 在 `migration_cpu_stop()` 失败时 `cpumask_set_cpu()`）。Juri Lelli 投票 option1；Peter 质疑「任何 set_cpus_allowed_ptr 都会遭同样问题，irq 为何特殊」并要求完整故障图（是否 migrate_disable + hotplug 组合、TLA+ 模型需扩展）。

## 背景与问题

（承接 20261003-008）IRQ 亲和性变更后 IRQ-core 置 `IRQTF_AFFINITY` 并唤醒中断线程，线程调 `set_cpus_allowed_ptr()` 更新掩码；选中 CPU 虽在线，但 `affine_move_task()` 走 stopper/`migration_cpu_stop()` 期间该 CPU 可能下线，`__migrate_task()` 被 `is_cpu_allowed()` 拒绝后返回当前 rq（与 `cpus_mask` 不符），随后 `migrate_disable()->schedule()` 改 `cpus_ptr` 使 `migrate_enable()` 期望的 `migration_pending` 为空。作者表示可回溯到 v6.8，即 migrate-disable 起就有。

## 技术方案

（承接 20261003-008）v2 实现两选项：(1) `irq_thread_check_affinity()` 里用 `scoped_guard(cpus_read_lock)` 包住 `set_cpus_allowed_ptr()`，保证迁移期间 CPU 不下线（作者论证无死锁：无 `synchronize_irq()` 等待线程完成）；(2) `migration_cpu_stop()` 里 `__migrate_task()` 失败时 `cpumask_set_cpu(rq->cpu, &p->cpus_mask)`，确保当前 CPU 仍在掩码内避免 migrate_enable 推任务（缺点：绕过 `set_cpus_allowed()` 回调、不更新 `nr_cpus_allowed`，可能破坏 SCHED_DEADLINE 不变量）。作者指出两者皆实现、取其一即可。

## 版本演进与当前进展

- v1（09-07，RFC + sashiko 质疑）→ v2（10-12，Repost 收集意见）。
- 今日 Juri 回帖「认同你的评估，看不到死锁，不走 set_cpus_allowed_dl 可能真有问题，投 option1」；Peter 回帖追问「其他 set_cpus_allowed_ptr 调用方是否同样受害、irq 为何特殊」，并要求 migrate_disable×hotplug 的完整图景（提及 Valentin 的 TLA+ 模型）。

## Maintainer 意见与讨论焦点

- **Juri Lelli**：投 option1（cpus_read_lock），认可作者无死锁论证，指出 option2 绕过 `set_cpus_allowed_dl()` 可能制造问题。
- **Peter Zijlstra**：质疑修复为何特化到 irq 路径（其他调用方也应受害），对「migrate_disable 发生在 hotplug 标记下线之后」的时序存疑，要求扩展 TLA+ 模型。

## 合入评估

*likelihood=medium*。真实竞态、有 syzbot 报告与双选项实现，但 Peter 对修复范围与完整故障图存疑，未定版。*blocking_issues*：Peter 的「为何 irq 特殊」之问、方案选择。*next_action*：作者回应 Peter 并收敛到 option1（Juri 已背书）。

## 效果评估

无性能数字；作者称可回溯到 v6.8、syzbot 报告（`syzbot+6835d5c11145e4f77057`）。正确性竞态修复。

## 我可以参与的点

- `discussion`：验证该竞态是否同样影响其他 `set_cpus_allowed_ptr()` 调用方（帮助回应 Peter 的问题）。
- `review`：评估 option2 的 `cpumask_set_cpu` 绕过回调对 SCHED_DEADLINE EDF 不变量与 `nr_cpus_allowed` 的影响。

## 参考链接

- lore（v2）: https://lore.kernel.org/all/20261012103946.aOSAmrRe@linutronix.de/
- lore（Juri 投票 option1）: https://lore.kernel.org/all/aszsZMSo9csAHNJu@jlelli-thinkpadt14gen4.remote.csb/
- lore（Peter 质疑）: https://lore.kernel.org/all/20261012143047.GV2009045@noisy.programming.kicks-ass.net/
