---
id: sched-20260806-011
date: "2026-08-06"
title: "sched/wake_q: 向 6.12.y 稳定分支回引 wake_q 辅助函数"
series: "Backport wake_q helper to stable 6.12.y"
type: fix
status: under_review
severity: low
merge_likelihood: high
tags: [wake_q, core_sched]
authors: ["Simon Liebold <simon.liebold@amd.com>", "John Stultz <jstultz@google.com>", "Waiman Long <longman@redhat.com>", "Peter Zijlstra <peterz@infradead.org>", "Ingo Molnar <mingo@kernel.org>"]
reviewers: ["John Stultz <jstultz@google.com>", "Waiman Long <longman@redhat.com>", "Peter Zijlstra <peterz@infradead.org>"]
related_articles: []
emails: ["uid-24225@qq-imap"]
---

# sched/wake_q: 向 6.12.y 稳定分支回引 wake_q 辅助函数

## 摘要

Simon Liebold（AMD）提交的 stable 回引：把上游 `wake_q` 辅助函数（用于延迟唤醒/锁释放后批量唤醒的模式）带回 **6.12.y** 稳定分支，以便后续修复或特性能在老稳定内核上统一使用，而不必每个下游各自重新实现。

要点：
- 这是对 `sched/wake_q.h` 相关辅助（如 `wake_q_add_safe`、`wake_up_q` 的封装变体）的稳定化回引，属于「基础设施先行」的 preparatory 提交。
- John Stultz、Waiman Long、Peter Zijlstra、Ingo Molnar 等参与 ack/review 链路（stable 回引常见流程：先 upstream 接受，再经 stable 邮件列表筛选）。
- 本日邮件（24225 等）主要是 stable 维护流程的往返（版本归属、Fixes 标记、依赖确认）。

## 技术细节

wake_q 机制：锁释放者把待唤醒任务放入 per-CPU `wake_q`，待退出临界区后一次性 `wake_up_q()`，避免持锁期间逐个 `try_to_wake_up()` 的多次 rq 锁获取。回引的辅助函数使 6.12.y 上的下游（如 RT/锁原语修复）能复用同一接口。

（注：稳定分支回引的具体 diff 以 stable 列表版本为准，本日邮件为流程类往返，未含新算法改动。）

## 影响与风险

- 影响面：仅 6.12.y 稳定分支的 `wake_q` 接口可用性与下游锁原语的二次开发；不影响主线行为（上游已合入）。
- 风险：低。纯稳定回引，无新逻辑；需确认依赖链完整、与 6.12.y 现有 `wake_q` 定义不冲突。
- 收益：让稳定分支具备与上游一致的延迟唤醒基础设施，便于后续 fix 的干净 backport。

## 评价

标准的 stable 准备性回引，reviewer 阵容为各相关子系统维护者。合入可能性高（走 stable 流程）。属基础设施类，本身无行为变更。
