---
id: sched-20261112-005
date: '2026-11-12'
subject: 'sched/wait: Queue non-exclusive waiters at the head in do_wait_intr*()'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20261111-b4-sched-wait-intr-head-v1-1-17cf2af5b964@columbia.edu>
lore_url: https://lore.kernel.org/all/20261111-b4-sched-wait-intr-head-v1-1-17cf2af5b964@columbia.edu/
authors:
- Mani Tofigh
maintainers_involved:
- Oleg Nesterov
current_version: v1
patch_series:
- version: v1
  msgid: <20261111-b4-sched-wait-intr-head-v1-1-17cf2af5b964@columbia.edu>
  date: '2026-11-11'
  summary: 非独占等待者插队头，避免被 EPOLLEXCLUSIVE 条目挡住而永久睡眠
  review_outcome: Oleg 认可并建议更彻底重构 __wait_event_interruptible_locked
upstream_commit: null
fixes_commit: 22c43c81a51e
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等维护者收取进 tip/sched/urgent 并走 stable 回退
contribution_opportunities:
- kind: testing
  description: 跑 reproducer 验证补丁后不再永久睡眠、独占等待者语义无回归
- kind: review
  description: 评估废弃 __wait_event_interruptible_locked 的重构是否值得跟进
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- wait
- hang
title: 'sched/wait: Queue non-exclusive waiters at the head in do_wait_intr*()'
layout: article
---

## TL;DR

Mani Tofigh 修一个可让任务永久睡眠的 waitqueue 缺陷：`wait_event_interruptible_locked_irq()`（eventfd/timerfd 用）把非独占读等待者加到队列尾部，若同一文件上先加了一个 `EPOLLEXCLUSIVE` 的 epoll 观察者，`__wake_up_common()` 唤醒独占条目后就停，被唤醒的 epoll 任务若被杀或离开而不读，读等待者就永远不醒。修复把 `do_wait_intr()/do_wait_intr_irq()` 的非独占加入改为插到队头（与 `prepare_to_wait_event()`/`add_wait_queue()` 一致）。带 `Cc: stable`；Oleg Nesterov 认可方向但建议更进一步直接废弃 `__wait_event_interruptible_locked()`。

## 背景与问题

`Fixes: 22c43c81a51e ("wait_event_interruptible_locked() interface")`，`Cc: stable`。eventfd/timerfd 用 `wait_event_interruptible_locked_irq()` 等待；`do_wait_intr_irq()` 把 reader 加到队列尾部，排在 `EPOLLEXCLUSIVE` 的 epoll 条目之后，而 `__wake_up_common()` 唤醒到独占条目即停。若被唤醒的 epoll 任务被杀掉或因故不读该文件，writer 的唤醒信号不会再被传递到排在其后的普通 reader——reader 永远睡眠，即使文件已可读；周期性 timerfd 也不会再唤它（timer 只在 read 时重启）。作者用确定性 hypervisor 确认，附 C reproducer（约 2 秒内命中）。

## 技术方案

单补丁：`do_wait_intr()` 与 `do_wait_intr_irq()` 里的非独占等待者改为插到队头——这正是 `__wake_up_common()` 依赖的顺序，`prepare_to_wait_event()`/`add_wait_queue()` 及 eventfd 切换 helper 前的旧实现都这么做。只改变非独占等待者的被唤醒顺序：每个等待者仍会收到每次唤醒。改动无性能影响。

## 版本演进与当前进展

*current_version: v1（2026-11-11，`<20261111-b4-sched-wait-intr-head-v1-1-17cf2af5b964@columbia.edu>`，11-12 北京时间收到）*。无版本演进。

## Maintainer 意见与讨论焦点

- **Oleg Nesterov**：认可「这看起来对，且与 `prepare_to_wait_event()` 一致」，但指出还有另一个问题——`WQ_FLAG_EXCLUSIVE` 时 `prepare_to_wait_event()` 里「Exclusive waiter must not fail if it was selected by wakeup」的既有注释；并建议「也许更合理的是直接杀掉 `__wait_event_interruptible_locked()`，把 `wait_event_interruptible_locked()` 基于 `___wait_event(cmd => do_wait_intr)` 重实现，这样 `do_wait_intr()` 只需 unlock + schedule + lock」。即认可本补丁但倾向更彻底的重构。
- 无 NAK。

## 合入评估

*likelihood=high*。修复小而正确、带 `Cc: stable` 与真实 reproducer，Oleg（waitqueue 资深维护者）方向认可。*blocking_issues*：无硬阻塞；Oleg 提的更彻底重构是可选的后继工作，不影响本修复先合入。*next_action*：等 Peter/Oleg 收取进 tip/sched/urgent 并走 stable 回退。

## 效果评估

作者给出确定性复现：eventfd/timerfd reader 在 `EPOLLEXCLUSIVE` 观察者不再读时永久睡眠；附 C reproducer 约 2 秒命中，补丁后 reader 被 write 正常唤醒。属正确性（hang 类）修复，无性能数据。

## 我可以参与的点

- **testing**：在 eventfd/timerfd + `EPOLLEXCLUSIVE` epoll 场景跑作者的 reproducer，验证补丁后不再永久睡眠；附带验证 `WQ_FLAG_EXCLUSIVE` 独占等待者语义未回归。
- **review**：评估 Oleg 提出的「用 `___wait_event` 重写 `wait_event_interruptible_locked()`、废弃 `__wait_event_interruptible_locked()`」重构是否值得作为后续 patch 跟进。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111-b4-sched-wait-intr-head-v1-1-17cf2af5b964@columbia.edu/
- Oleg 的评审: https://lore.kernel.org/all/avTzzxZvE3HqH3KS@redhat.com/
