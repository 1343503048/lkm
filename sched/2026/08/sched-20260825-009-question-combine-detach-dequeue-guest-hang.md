---
title: "[Question] 用户态限流 + 「Combine detach into dequeue」导致 guest 启动挂起"
date: 2026-08-25
tags: [sched/fair, crash, regression]
series: "combine detach dequeue guest boot hang"
type: bug
severity: high
status: under_review
lore: ""
---

## 概述

报告者（UID 57212 / 57225 / 57402）反馈：在开启用户态限流（userspace throttling，
如 cgroup cpu 限流）的场景下，配合主线提交 `sched/fair: Combine detach into dequeue
when migrating task`，会导致 **guest（虚拟机）启动挂起（boot hang）**。

怀疑点：该提交改变了迁移任务时的 detach/dequeue 合并行为，在受限流影响的 cgroup
下，detach 与 dequeue 合并后的时序/锁顺序变化，使 guest 引导路径上的某个任务迁移
陷入等待，最终表现为启动卡死。

## 触发条件

- 配置：对 guest 相关 cgroup 施加 userspace/CPU 限流（throttling）。
- 内核：含 `Combine detach into dequeue when migrating task` 的较新主线。
- 现象：guest 启动过程中挂起，无继续进展。

## 状态与讨论

- 当前状态：**under_review / 问题报告阶段**（以 `[Question]` 形式提出，等待维护者
  确认是否与目标提交存在因果）。
- 严重度：**high**（guest 无法启动，影响可用性）。
- 需确认：是否为该提交的回归、是否主线可稳定复现、是否有最小复现脚本。

## 关联

- 011 sched/fair：update_curr_eevdf 用于剩余 root cfs_rq 调用方（EEVDF 清理）
- 007 sched：nr_pinned per-CPU 计数器（迁移相关）
