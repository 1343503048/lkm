---
id: sched-20261003-008
date: '2026-10-03'
subject: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: <20260907085825.f-CZ1Q5y@linutronix.de>
lore_url: https://lore.kernel.org/all/20261002160701.7Pqp05o3@linutronix.de/
authors:
- Sebastian Andrzej Siewior
maintainers_involved: []
current_version: rfc
patch_series:
- version: rfc
  msgid: <20260907085825.f-CZ1Q5y@linutronix.de>
  date: '2026-09-07'
  summary: CPU 热插拔 vs set_cpus_allowed_ptr() 竞态 RFC（两条互斥修法）
  review_outcome: 10-03 回应死锁与语义疑虑，提出 bit+do_set_cpus_allowed() 新方向
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 修法方向未收敛（三条候选路径）
  - 无 maintainer review（近一个月）
  next_action: 把 do_set_cpus_allowed() 方向落成 RFC v2 补丁
contribution_opportunities:
- kind: review
  description: 审计 CPU down 路径是否存在隐藏的中断线程等待点，补证据验证死锁证伪论断
- kind: new_patch
  description: 把置位+do_set_cpus_allowed() 方向做成 RFC v2 补丁并验证 DL admission 语义
generated_at: '2026-10-04T01:00:00'
source_email_count: 1
related_articles:
- sched-20260907-002
tags:
- hotplug
- migration
- irq
title: 'sched: irq: cpu-hotplug race vs set_cpus_allowed_ptr()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-002-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20260907-002</a>：Sebastian Andrzej Siewior（linutronix）09-07 发出 RFC——syzbot 报出的 CPU 热插拔与 `set_cpus_allowed_ptr()` 竞态：IRQ 线程请求迁移到「当时在线但可能马上掉线」的 CPU，`__migrate_task()` 被 `is_cpu_allowed()` 拒掉后返回当前 rq，任务所在 CPU 与 `cpus_mask` 不再匹配，后续 `migrate_enable()` 改亲和性而 `affine_move_task()` 等不到 `migration_pending`。他给了两条互斥修法（IRQ 侧持 `cpus_read_lock`；或 `migration_cpu_stop()` 失败时把当前 CPU 补进 `cpus_mask`），称能复现到 v6.8、「大概从 migrate-disable 诞生第一天就在」。
- <a class="article-ref" href="/lkm/2026/10/03/sched-20261003-008-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20261003-008</a>（今天）：Sebastian 时隔近一个月回帖推进，回应外部对死锁与语义的两个疑虑（原始提问邮件未入本缓存，以下据其引用转述）：(1) **死链指控不成立**——CPU down 路径的 `cpus_write_lock()` 与 `irq_migrate_all_off_this_cpu()`/`irq_thread_check_affinity()` 的 `cpus_read_lock()` 之间没有 `synchronize_irq()` 等待中断线程完成，中断线程只是阻塞在 `cpus_read_lock()` 直到 CPU down 完成，不构成死锁；(2) **`__migrate_task()` 失败后 fallback `cpumask_set_cpu()` 强改 `p->cpus_mask` 的疑虑**（跳过 `set_cpus_allowed()` 回调、不更新 `nr_cpus_allowed`、可能破坏 SCHED_DEADLINE 全局 EDF 不变量）——Sebastian 确认该路径「成功与否不可知」，问题限于 migrate-disable 场景，并提出新方向：「Maybe set the bit followed by do_set_cpus_allowed()?」。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/07/sched-20260907-002-sched-irq-cpu-hotplug-race-vs-set-cpus-allowed-ptr.html">sched-20260907-002</a>）触发链条：IRQ 亲和性变更 → 中断线程 `set_cpus_allowed_ptr()` 请求迁移 → 迁移期间目标 CPU 掉线 → `__migrate_task()` 因 `is_cpu_allowed()` 拒绝返回任务当前 rq → 任务所在 CPU 与 `cpus_mask` 失配 → 之后 `migrate_disable() -> schedule()` 触发的 `migrate_enable()` 期望 `migration_pending` 已置位而实际为 NULL。主线代码在 `migration_cpu_stop()` 附近本有自认软肋注释（`XXX __migrate_task() can fail, at which point we might end up running on a dodgy CPU`），作者 9 月的 RFC 给出「it *is* a big deal」实例。

今天新增的焦点是被引用方提出的语义疑虑：CPU down 期间 `migration_cpu_stop()` 的 fallback 直接 `cpumask_set_cpu(cpu, &p->cpus_mask)`——绕过 `p->sched_class->set_cpus_allowed()` 类回调（如 `set_cpus_allowed_dl()` 的 admission control）且不更新 `p->nr_cpus_allowed`，理论上可让非特权任务逃出 cpuset 亲和边界、破坏 DL 全局 EDF 不变量。

## 技术方案

（承接 v1 RFC 的两条互斥修法）今天的新增讨论：

- **死锁辨析**：`cpus_write_lock()`（CPU down）vs `cpus_read_lock()`（`irq_thread_check_affinity()`）不构成 ABBA——没有 `synchronize_irq()` 等待中断线程完成这一环；掩码更新、线程唤醒、线程在 `cpus_read_lock()` 上阻塞到 CPU down 结束，安全。
- **fallback 语义修补方向**：Sebastian 观察「不是所有调用方都持 hotplug 锁、也确实不知道 `do_set_cpus_allowed()` 是否成功」，问题面限于 migrate-disable；不带 migrate-disable 时 wake-up 路径会打印 "process … no longer affine to cpu" 自选 CPU 兜底。提出的新方向是**先置位掩码、再走 `do_set_cpus_allowed()`**（完整类回调语义），替代裸 `cpumask_set_cpu()`。

## 版本演进与当前进展

- RFC v1（09-07，`<20260907085825.f-CZ1Q5y@linutronix.de>`）：两条互斥修法示意（「one is enough」）。
- 10-03（`<20261002160701.7Pqp05o3@linutronix.de>`）：回应死锁与语义疑虑，提出「set the bit followed by do_set_cpus_allowed()」方向。无新补丁版本。

## Maintainer 意见与讨论焦点

- 提问方（sashiko，原始邮件未入缓存）的两个疑虑：CPU down 死链风险；fallback 绕过 `set_cpus_allowed()` 回调的 DL/cpuset 语义破坏。Sebastian 逐点回应：前者证伪，后者承认并给方向。
- Peter Zijlstra 全程未表态（RFC 近一个月无 maintainer 介入，卡在「修法方向选择」）。

## 合入评估

*likelihood=low*。RFC 近一个月、无 maintainer 表态、两条原修法未收敛、今天又引入第三个方向（bit + do_set_cpus_allowed()）；无新补丁版本。*blocking_issues*：修法方向未定（`cpus_read_lock` 侧修 vs stopper 侧补掩码 vs do_set_cpus_allowed() 完整语义）；无 maintainer review。*next_action*：作者把「set the bit followed by do_set_cpus_allowed()」落成补丁并发 RFC v2。

## 效果评估

（承接 v1）syzbot 复现、可追到 v6.8。今天为纯讨论（死锁辨析 + 语义方向），无新数据。死锁指控的证伪依据是「无 `synchronize_irq()` 等待环」，属代码路径论证而非实测。

## 我可以参与的点

- `review`：验证「CPU down 无 `synchronize_irq()` 等待中断线程」的论断——审计 `irq_migrate_all_off_this_cpu()`/`smpcfd_prepare_cpu()` 等路径是否存在隐藏等待点，回帖补证据（该论断目前只有单人论证）。
- `new_patch`：把「置位 + `do_set_cpus_allowed()`」方向做成 RFC v2 补丁（Sebastian 尚未落码），并在 DL 侧验证 admission control 语义。

## 参考链接

- lore（Sebastian 10-03 回复）: https://lore.kernel.org/all/20261002160701.7Pqp05o3@linutronix.de/
- lore（09-07 RFC 原文）: https://lore.kernel.org/all/20260907085825.f-CZ1Q5y@linutronix.de/
