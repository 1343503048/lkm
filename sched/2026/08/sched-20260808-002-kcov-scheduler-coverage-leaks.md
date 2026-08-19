# kcov scheduler coverage leaks

## 概述

Marco Elver 提交 5 片系列，抑制 KCOV（内核覆盖率工具）在定时器与调度器路径上的覆盖"泄漏"，使 syscall 覆盖率保持输入相关、不被内核自身调度/定时器路径污染。

## 背景与问题

KCOV 默认排除中断与调度器覆盖，使 syscall 覆盖率保持输入相关。但被插桩的被调用函数仍会在未插桩的定时器与调度器路径（`in_task()` 为 true）运行时记录覆盖，造成"泄漏"。

## 变更内容（调度相关片）

- **3/5 sched: pause KCOV in `__schedule()`**：在调度核心路径暂停 KCOV 收集。
- **4/5 sched: pause KCOV in `try_to_wake_up()`**：在唤醒路径暂停。
- **5/5 sched: pause KCOV in `wake_up_new_task()`**：在新任务唤醒路径暂停。
- 0/5 cover 描述整体动机；1/5（非 sched）、2/5 等其他片处理定时器侧。

## 评审

收到多方 Re（Peter Zijxstra 等就实现细节讨论），属工具侧改进，对调度功能无行为影响，仅缩小覆盖率采集范围。

## 状态

v1，处于评审阶段。

## 参考链接

- 系列：uid 27674 / 27678 / 27675 / 27679

---
subject: "kcov: 抑制定时器与调度器覆盖泄漏"
date: 2026-08-08
series: "kcov-scheduler-coverage-leaks"
version: "v1"
status: "in-review"
tags: [sched/core, idle]
related_articles: []
submitter: "Marco Elver"
emails:
  - uid: 27674
    subject: "[PATCH 0/5] kcov: suppress timer and scheduler coverage leaks"
  - uid: 27678
    subject: "[PATCH 3/5] sched: pause KCOV in __schedule()"
  - uid: 27675
    subject: "[PATCH 4/5] sched: pause KCOV in try_to_wake_up()"
  - uid: 27679
    subject: "[PATCH 5/5] sched: pause KCOV in wake_up_new_task()"
---
