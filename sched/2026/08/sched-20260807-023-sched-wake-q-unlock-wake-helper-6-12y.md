# arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS

## 概述

针对提交到 6.12.y 稳定分支的 `raw_spin_unlock*_wake()` helper backport（上游 commit `abfdccd6af2b`），评审者提出封面信理由站不住脚的质疑，并分析其在 6.12.y 上的实际行为。

## 背景

上游新增 helper 以清理常见模式：

```c
preempt_disable();
raw_spin_unlock(lock);
wake_up_q(wake_q);
preempt_enable();
```

封装为 `raw_spin_unlock*_wake()`。封面信称其"虽像重构，但加了 `if (wake_q)` 门控唤醒队列排空"。

## 评审观点

- 该 `if (wake_q)` 是 NULL 指针检查，而非"队列是否为空"检查。在 6.12.y 上每个调用点都传入栈上 `DEFINE_WAKE_Q` 的地址（`__mutex_unlock_slowpath()` 与 `task_blocks_on_rt_mutex()` 都无条件传 `&wake_q`），故永不为 false，preempt_disable + wake_up_q 排空与现状完全一致。唯一可能传 NULL 的是 `rt_mutex_slowlock_block()` 经 `rt_mutex_wait_proxy_lock()`，而该路径已在 6.12.y 通过 `4a0779145781` 的 backport 自带相同守卫。
- 第 1/2 片还将 `mutex::wait_lock` 改为 irqsave/irqrestore，反而给慢路径增加少量成本而非移除。

结论：机械上两片可干净应用到 6.12.y，但封面信理由不成立，需修订说明。

## 状态

稳定分支 backport 评审中，待修订封面信。

## 参考链接

- 邮件：uid 25292

---
subject: "sched/wake_q: 6.12.y 上 raw_spin_unlock*_wake() helper 的 backport 评审"
date: 2026-08-07
series: "sched-wake-q-unlock-wake-6-12y"
version: "v1"
status: "in-review"
tags: [wake_q, affinity]
related_articles: []
submitter: "社区（6.12.y stable backport 评审）"
emails:
  - uid: 25292
    subject: "Re: [PATCH 6.12.y 1/2] locking: Add raw_spin_unlock*_wake() helpers"
---
