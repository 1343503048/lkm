---
title: "tip/sched/urgent 合入两笔修复：Skip rq->avg_idle + x86/itmt 去 debugfs 依赖"
date: 2026-09-02
tags: [sched/core, compatibility]
series: "tip sched urgent avg idle itmt"
type: fix
severity: medium
status: merged_tip
lore: ""
---

## 概述

09-02 `tip/sched/urgent` 合入两笔修复，分别来自调度核心与 x86 调度相关代码：

1. `sched/core: Skip rq->avg_idle update without a valid idle_stamp`（UID 73124）：
   在没有有效 `idle_stamp` 时跳过 `rq->avg_idle` 更新，避免用陈旧/无效时间戳计算
   idle 均值。
2. `x86/itmt: Don't make ITMT enablement depend on debugfs`（UID 73115）：
   x86 ITMT（Intel Turbo Boost Max Technology）的启用此前依赖 debugfs 是否挂载，
   改为不依赖，确保在无 debugfs 的生产环境也能正确启用 ITMT 调度偏好。

## 改动内容 / 核心补丁

- 见概述两条 `[tip: sched/urgent]` 提交。

## 状态与讨论

- 当前状态：**merged_tip**（已进入 `tip/sched/urgent`）。
- 合入可能性：**high/已合入**。两笔均为小型正确性/健壮性修复。

## 关联

- 002 PREEMPT_DYNAMIC 简化（同属 tip 当天批量）
