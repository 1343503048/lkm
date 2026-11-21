# sched: Reset cpumask if __migrate_task() failed for migration_cpu_stop()

## TL;DR

Sebastian Andrzej Siewior 发 v3 修 syzbot 报的竞态：IRQ 亲和性变更与 CPU hotplug 并发时，`affine_move_task()` 里 `__migrate_task()` 因目标 CPU 下线而失败，任务停在当前 rq 但 `cpus_mask` 仍指向旧 mask，后续 `migrate_enable()` 因 `migration_pending` 为 NULL 触发出错。补丁在 `__migrate_task()` 失败时用 `do_set_cpus_allowed()` 把任务 mask 重置为当前所在 rq。Karl Mehltretter 复测确认 syzbot 警告消失，但又发现该路径二次更新 rq clock 触发 `WARN_DOUBLE_CLOCK`，说明 v3 仍需改进。

## 背景与问题

IRQ 亲和性被改后，IRQ core 置 `IRQTF_AFFINITY` 并唤醒中断线程去 `set_cpus_allowed_ptr()` 更新 mask。该 CPU 已被验证 online，但没保证它在 `affine_move_task()` 迁移期间保持 online——迁移走 stopper/`migration_cpu_stop()`，任务暂停时若 CPU 下线，`is_cpu_allowed()` 拒绝导致 `__migrate_task()` 返回当前 rq（与 `cpus_mask` 不匹配）。此后 `migrate_disable()`→`schedule()` 改 `cpus_ptr`，`migrate_enable()` 期望 `migration_pending` 非 NULL 却实际为 NULL。syzbot 报告触发；Karl 在 PREEMPT_RT + syzbot config 下复现：未打补丁每次 boot 都 WARN，有一次还命中 `kernel BUG at kernel/sched/core.c:3642!`（`select_fallback_rq()`）导致 panic。

## 技术方案

在 `__migrate_task()` 失败时，用 `do_set_cpus_allowed()` 把任务 CPU mask 重置为它当前所在的 runqueue（而非仅改 `cpus_mask` 字段），这样还会走各调度类的 `set_cpus_allowed` 回调；同时删除原先关于 `__migrate_task()` 失败的注释。作者说明 IRQ 线程场景下 CPU 下线后本身还有一次更新，故无需 `cpus_read_lock()` 阻塞 hotplug。

## 版本演进与当前进展

*current_version: v3（2026-11-20 发出，`<20261120171658.Cf9qIU-Y@linutronix.de>`，单补丁）*。当日无新版本；进展来自两位复测者的反馈。本日缓存未见 v1/v2 原文（或被过滤），首条新回帖为 Karl Mehltretter 的复测。

## Maintainer 意见与讨论焦点

- **Karl Mehltretter（复测，非维护者）**：确认补丁消除 syzbot 警告；并指出另一问题——`do_set_cpus_allowed()` 经 `sched_change_begin()`（不带 `DEQUEUE_NOCLOCK`）二次更新 rq clock，在开 `WARN_DOUBLE_CLOCK` 时触发 `update_rq_clock()` 的 WARNING（v7.4-rc3，RT 与非 RT 均可复现，用 `sched_setaffinity()` 循环 + `smt/control` 开关）。另观察到 `sched_setaffinity()` 属同类竞态点之一，但用户任务不会像 IRQ 线程那样得到后续更新。
- 无 NAK；核心思路未被否定，但实现引出新的右环问题。

## 合入评估

*likelihood=medium*。修复方向正确且获复测背书（syzbot 警告消失），但 `do_set_cpus_allowed()` 引入的 rq clock 二次更新（`WARN_DOUBLE_CLOCK`）须先解决，否则带该 config 测不过。*blocking_issues*：`do_set_cpus_allowed()` 重复更新 rq clock；`sched_setaffinity()` 一处未覆盖的同类竞态。*next_action*：作者改走不二次 `update_rq_clock()` 的路径（或复用已有 clock 更新），并评估是否顺带修 `sched_setaffinity()` 竞态。

## 效果评估

复测者数据：PREEMPT_RT + syzbot config 下打补丁后 syzbot 警告消失（不打则每 boot 都 WARN，一次 panic）；用户线程亲和性测试中打补丁后约 1/5000 次读到 mask 之外的 CPU（RT 与非 RT 均复现），不打补丁永不。均为复测者自测。

## 我可以参与的点

- **review**：确认 `do_set_cpus_allowed()` 在此上下文（stopper 内）是否适合复用已有 rq clock 更新、避免 `WARN_DOUBLE_CLOCK`。
- **testing**：在非 RT / sysrq-hotplug 与 `sched_setaffinity()` 循环下复测 mask 落点与告警。
- **extend**：基于作者指出的 `sched_setaffinity()` 同类竞态补一版后续 patch。

## 参考链接

- lore thread（v3 patch）: https://lore.kernel.org/all/20261120171658.Cf9qIU-Y@linutronix.de/
- Karl 复测（WARN_DOUBLE_CLOCK）: https://lore.kernel.org/all/20261121132023.41237-1-kmehltretter@gmail.com/

---
id: sched-20261121-002
date: '2026-11-21'
subject: "sched: Reset cpumask if __migrate_task() failed for migration_cpu_stop()"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261120171658.Cf9qIU-Y@linutronix.de>"
lore_url: "https://lore.kernel.org/all/20261120171658.Cf9qIU-Y@linutronix.de/"
authors: [Sebastian Andrzej Siewior]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261120171658.Cf9qIU-Y@linutronix.de>"
    date: '2026-11-20'
    summary: "在 __migrate_task() 失败时用 do_set_cpus_allowed() 重置 mask 到当前 rq"
    review_outcome: "Karl 复测 syzbot 警告消失，但发现 WARN_DOUBLE_CLOCK"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["do_set_cpus_allowed() 二次更新 rq clock 触发 WARN_DOUBLE_CLOCK", "sched_setaffinity() 同类竞态未覆盖"]
  next_action: "作者改走不复用二次 update_rq_clock 的路径并重发"
contribution_opportunities:
  - kind: review
    description: "确认 do_set_cpus_allowed() 在 stopper 内如何避免二次 update_rq_clock"
  - kind: testing
    description: "非 RT + sysrq hotplug + sched_setaffinity 循环复测 mask 落点与告警"
  - kind: extend
    description: "为作者指出的 sched_setaffinity() 同类竞态补后续 patch"
generated_at: "2026-11-22T01:00:00+08:00"
source_email_count: 91
related_articles: []
tags: [affinity, preempt, syzbot]
---