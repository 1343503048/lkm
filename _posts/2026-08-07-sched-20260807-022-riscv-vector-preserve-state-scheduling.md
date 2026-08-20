---
subject: 'riscv: 在非零 Vector 嵌套深度调度时保留 Vector 状态'
date: 2026-08-07
series: riscv-vector-preserve-state
version: v1
status: in-review
tags:
- riscv
- sched/fair
related_articles: []
submitter: Karl Mehltretter
emails:
- uid: 25457
  subject: '[PATCH] riscv: vector: preserve state when scheduling at nonzero depth'
title: 'riscv: 在非零 Vector 嵌套深度调度时保留 Vector 状态'
layout: article
---

## 概述

Karl Mehltretter 修复 RISC-V 在非零 Vector 嵌套深度发生调度时，`IN_SCHEDULE` 快捷路径导致 Vector 状态丢失、进而静默破坏用户数据的问题。

## 问题

`IN_SCHEDULE` 快捷路径让 `__switch_to_vector()` 在自愿调度点（Vector 寄存器为 caller-saved）丢弃 Vector 状态，switch-in 无需恢复即可启用 Vector。但中断或 fault 也可在非零 Vector 嵌套深度触发调度，此时触发：

```
WARNING: arch/riscv/include/asm/vector.h:376 at __schedule+0xfbc/0x10b4
```

快捷路径同样在 switch-in 被采用，跳过 `NEED_RESTORE`，`riscv_v_context_nesting_end()` 以陈旧 Vector 寄存器恢复。在 vectorized usercopy 循环中，`vsetvli` 与 `vle8.v/vse8.v` 之间的中断可让任务以另一任务的 vl/vtype/Vector 寄存器恢复——标量循环状态存活，但拷贝可能用错 vector length，**静默破坏用户数据**。vectorized usercopy 中的睡眠缺页在没有 `CONFIG_PREEMPTION` 时也可到达同一 switch。

## 修复

仅在 depth 0 使用快捷路径；非零深度切换保留既有的 save 与 `NEED_RESTORE` 行为。

## 状态

v1，处于评审阶段（属调度相关的架构状态保存修复）。

## 参考链接

- 邮件：uid 25457
