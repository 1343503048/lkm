## 概述

“Flatten the pick”是一轮关于把调度器选核（pick）路径从多层嵌套调用扁平化、
减少间接层与锁/重算开销的持续讨论。本期以 v3 的回复形式推进
（Re: UID 55314 / 55494），聚焦设计取舍与瓶颈点。

## 改动内容 / 核心补丁

- 讨论将 pick_next_task / select_task_rq 等相关调用链扁平化，降低逐层回溯成本。
- 涉及与 EEVDF、delayed entity、cgroup 任务组更新锁（见 005）的相互影响。

## 状态与讨论

- 当前状态：**discussion（讨论中）**，尚无合并结论。
- 属于跨多日的架构级讨论，本期为 v3 评审意见与修订方向交流。

## 关联

- 005 sched：cgroup 更新锁上提到 core
- 011 sched/fair：ENQUEUE_DELAYED / place_entity 调整
- 009 sched/cache：active load balance 中尊重 migrate_llc_task

---
title: "sched：Flatten the pick —— 调度选核路径扁平化讨论"
date: 2026-08-24
tags: [sched/core, sched/fair, discussion]
series: "flatten the pick"
type: discussion
severity: medium
status: discussion
lore: ""
---
