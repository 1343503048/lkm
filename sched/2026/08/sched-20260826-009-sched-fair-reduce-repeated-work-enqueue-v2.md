---
title: "sched/fair：减少 enqueue 路径上的重复工作（v2）"
date: 2026-08-26
tags: [sched/fair, eevdf]
series: "reduce repeated work in enqueue path"
type: fix
severity: low
status: under_review
related_articles: ["sched-20260824-011-sched-fair-reuse-enqueue-delayed.md", "sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）

EEVDF 的 `enqueue_task_fair()` 中，`flags & ENQUEUE_DELAYED` 的检查散落多处。本期 v2
（UID 59093 0/2 封面、59098 1/2、59055 2/2，含 Re: 59154）把该判断集中成一个在
函数开头计算的布尔量 `delayed`，消除重复判定。

v2 的 1/2（据 59093 正文）核心改动：
```c
-       bool curr;
+       bool curr, delayed = (flags & ENQUEUE_DELAYED);
...
-       if (!p->se.sched_delayed || (flags & ENQUEUE_DELAYED))
+       if (!p->se.sched_delayed || delayed)
                util_est_enqueue(cfs_rq, p);
        update_curr_  eevdf(cfs_rq);
-       if (flags & ENQUEUE_DELAYED) {
+       if (delayed) {
                requeue_delayed_entity(cfs_rq, se);
                return;
        }
```
声明「无功能变更（No functional change intended）」。2/2 进一步在 `place_entity()` 与
`requeue_delayed_entity()` 中避免对 `curr` 状态做重复计算。

## 改动内容 / 核心补丁

- 1/2 reuse the ENQUEUE_DELAYED calculation in enqueue_task_fair()：把 ENQUEUE_DELAYED
  判断收敛为局部布尔 `delayed`。
- 2/2 avoid recalculating curr status in place_entity() and requeue_delayed_entity()：
  去除重复的状态重算。

## 状态与讨论

- 当前状态：**under_review**（v2，相对 08-24 的初版迭代）。
- 合入概率 medium；属于 fair/EEVDF 内部一致性清理，风险低。

## 关联

- 08-24 011 复用 ENQUEUE_DELAYED 初版
- 08-25 011 update_curr_eevdf 用于剩余 root cfs_rq 调用方
- 005（同日）hrtick 重启动（同为 fair 类修正）
