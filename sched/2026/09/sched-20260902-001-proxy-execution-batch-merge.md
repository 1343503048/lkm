---
title: "Proxy Execution 一批改动合入 tip/sched/core"
date: 2026-09-02
tags: [proxy_execution, sched/core]
series: "proxy execution batch merge tip"
type: feature
severity: medium
status: merged_tip
lore: ""
---

## 概述

Proxy Execution（PE，解决优先级翻转 / 锁持有者代理运行）在 09-02 有一批改动合入
`tip/sched/core`，是 PE 主线化进程的又一次重要推进。同日另有独立补丁
`sched/core: fix task_sched_runtime() for proxy execution`（UID 73816）也属该方向。

## 改动内容 / 核心补丁（合入 tip/sched/core 的提交）

- `sched: Migrate whole chain in proxy_migrate_task()`
- `sched: Switch rq->next_class in proxy_reset_donor()`
- `sched/core: Don't proxy-exec unmatched cookie lock owners`（UID 73210）
- `sched/core: Don't steal a proxy-exec donor`（UID 73240）
- `sched/core: Avoid migrating blocked_on tasks`（UID 73217）
- `sched: Break out core of attach_tasks() helper into sched.h`（UID 73236）
- `sched/core: fix task_sched_runtime() for proxy execution`（UID 73816，独立补丁）

## 状态与讨论

- 当前状态：**merged_tip**（已进入 `tip/sched/core`，待后续合并窗口进入主线）。
- 合入可能性：**high/已合入**。
- 与 08-26 的「PROXY_EXEC 备选方案 RFC PoC（16 补丁）」是不同路线：本批是主线既有
  PE 实现的增量修复与清理，并非那套备选方案。

## 关联

- 08-26 007 PROXY_EXEC 备选方案 RFC PoC（不同路线）
