## 概述

在基于 v4.19 的厂商内核上，`pick_next_task_fair()` 中触发了空指针解引用
（NULL deref）崩溃（UID 54535）。该问题可能与 delayed/deadline 实体或 cgroup
任务组在负载均衡/抢占路径上的状态不一致有关。

## 改动内容 / 核心补丁

- 报告并定位崩溃现场，给出复现条件与调用栈。
- 讨论是否为主线也存在、还是仅限 v4.19 厂商分支的回归/缺补丁问题。

## 状态与讨论

- 当前状态：**under_review / 报告阶段**。
- 注意：v4.19 为长期支持厂商分支，是否主线可复现需验证；往日类似报告亦多标记为
  “vendor-only，可能不重现于主线”，需谨慎归因。

## 关联

- 007 sched/core：arm64 偶发 stale rq->curr
- 011 sched/fair：ENQUEUE_DELAYED / place_entity 调整

---
title: "sched/fair：v4.19 厂商内核中 pick_next_task_fair 空指针解引用"
date: 2026-08-24
tags: [crash, sched/fair, compatibility]
series: "NULL deref pick_next_task_fair v4.19"
type: bug
severity: high
status: under_review
lore: ""
---
