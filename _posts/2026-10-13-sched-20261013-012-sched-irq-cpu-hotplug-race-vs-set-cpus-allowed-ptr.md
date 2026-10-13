---
id: sched-20261013-012
subject: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
date: 2026-10-13
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
- version: v2
  msgid: <20261012103946.aOSAmrRe@linutronix.de>
  date: 2026-10-12
  summary: option1 cpus_read_lock 包 set_cpus_allowed_ptr；option2 migration_cpu_stop
    失败时 cpumask_set_cpu
  review_outcome: Juri 投票 option1；Peter 质疑 irq 特殊性并要求故障图，作者取证中
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 对「irq 为何特殊」的质疑未答，故障图尚未给出
  next_action: 作者用 reproducer/tracepoint 给出准确故障图，收敛 option 选择
contribution_opportunities:
- kind: testing
  description: 协助复现 migrate_disable + CPU hotplug 竞态并提供 tracepoint 证据
- kind: discussion
  description: 分析该竞态是否对所有 set_cpus_allowed_ptr 调用方通用，界定修复范围
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261003-008
- sched-20261012-013
tags:
- affinity
title: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
layout: article
---

> **subject**：sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-002-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20260907-002</a> / 20261003-008：Sebastian Siewior 的 RFC——syzbot 报出的 CPU 热插拔与 `set_cpus_allowed_ptr()` 竞态：IRQ 线程迁移到「当时在线但可能马上掉线」的 CPU，`__migrate_task()` 被 `is_cpu_allowed()` 拒后返回当前 rq，任务所在 CPU 与 `cpus_mask` 失配。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-013-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20261012-013</a>：作者发 v2（option1 在 `irq_thread_check_affinity()` 里 `scoped_guard(cpus_read_lock)`；option2 在 `migration_cpu_stop()` 失败时 `cpumask_set_cpu()`）；Juri 投票 option1，Peter 质疑「任何 set_cpus_allowed_ptr 都会遭同样问题、irq 为何特殊」并要求完整故障图。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-012-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20261013-012</a>（今天）：Sebastian 回应 Peter——「这不是特殊情况」，准备抓 reproducer 和几个 tracepoint 画出准确故障图；凭记忆描述的故障路径（CPU0 上 migrate_disable 的任务被分配到 CPU1、schedule；CPU1 将下线而 CPU0 上的任务返回并 migrate_enable 应迁往 CPU1），并声明「给我复现器、回头再答」。

## 背景与问题
（承接 20260907-002 → 20261012-013）IRQ 亲和性变更 → 中断线程 `set_cpus_allowed_ptr()` 请求迁移 → 迁移期间目标 CPU 下线 → `__migrate_task()` 因 `is_cpu_allowed()` 拒绝返回任务当前 rq → 任务 CPU 与 `cpus_mask` 失配 → 之后 `migrate_disable()->schedule()` 触发的 `migrate_enable()` 期望 `migration_pending` 已置位而实际为 NULL。主线代码在 `migration_cpu_stop()` 附近本就有自认软肋注释（`XXX __migrate_task() can fail ...`）。可回溯到 v6.8（migrate-disable 起就存在）。

## 技术方案
（承接 20261012-013）v2 两选项：option1 `irq_thread_check_affinity()` 里 `scoped_guard(cpus_read_lock)` 包住 `set_cpus_allowed_ptr()`；option2 `migration_cpu_stop()` 失败时 `cpumask_set_cpu()`。今天无新代码，Sebastian 的进展是：接受 Peter「画出完整故障图」的要求，准备抓 reproducer + tracepoint 确认「目标 CPU 掉线时 CPU0 上 migrate_disable 任务、assignment 到 CPU1、schedule、migrate_enable 应迁往 CPU1」这条链路的精确时序。

## 版本演进与当前进展
当前 v2（`<20261012103946.aOSAmrRe@linutronix.de>`），无新版本；今日作者推进诊断取证（reproducer + tracepoint），回应 Peter 的完整性要求。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（前日）：质疑「irq 为何特殊」「任何 set_cpus_allowed_ptr 都会遭同样问题」，要求完整故障图（是否 migrate_disable + hotplug 组合）。
- **Juri Lelli**（前日）：投 option1（IRQ 侧持 `cpus_read_lock`）。
- **Sebastian Siewior**（作者，今日）：认为「not special」，正取证画准确图，暂不提交修改。

## 合入评估
*likelihood=medium*。v2 已出、有 Juri 投票 option1，但 Peter 对「irq 特殊性」的质疑与故障图尚未闭环，作者仍在取证。*blocking_issues*：Peter 的完整性疑问未答；结论（是否只修 IRQ 侧、还是通用问题）未定。*next_action*：作者用 reproducer/tracepoint 给出准确故障图，回应 Peter 后收敛 option 选择。

## 效果评估
无性能/复现数据变更；本轮为诊断取证阶段。

## 我可以参与的点
- testing：可协助用 PREEMPT_RT 环境复现「migrate_disable 任务 + CPU hotplug」竞态，提供 tracepoint 证据。
- discussion：分析该竞态是否如 Peter 所疑「对所有 set_cpus_allowed_ptr 调用方通用」，帮助界定修复范围（IRQ 侧 vs 通用 migration_cpu_stop 路径）。

## 参考链接
- v2 线程 lore：https://lore.kernel.org/all/20261012103946.aOSAmrRe@linutronix.de/
- 今日回帖：https://lore.kernel.org/all/20261013064617.jw7Sk6un@linutronix.de/
