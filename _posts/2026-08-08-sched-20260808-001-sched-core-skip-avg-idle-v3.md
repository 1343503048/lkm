---
subject: 'sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新（v3）'
date: 2026-08-08
series: sched-core-skip-avg-idle
version: v3
status: in-review
tags:
- sched/core
- idle
related_articles:
- sched-20260807-019-sched-core-skip-avg-idle-no-idle-stamp
submitter: Shubhang Kaushik (Ampere)
emails:
- uid: 27672
  subject: '[PATCH v3] sched/core: Skip rq->avg_idle update without a valid idle_stamp'
- uid: 27645
  subject: 'Re: [PATCH v2] sched/core: Skip rq->avg_idle update without a valid idle_stamp'
title: sched core skip avg idle v3
layout: article
---

## 概述

本篇为 8/7 系列 **019**（`sched-core-skip-avg-idle`）的 v3 迭代，延续修复 `update_rq_avg_idle()` 在无有效 idle 间隔时错误驱动 `rq->avg_idle` 到钳位值的问题。

## 版本演进（v2 → v3）

- 描述 `sched_balance_newidle()` / `ttwu_pending` 路径作为"进入 idle 但 `idle_stamp` 为零"的示例（sched_balance_newidle 在 `this_rq->ttwu_pending` 置位时提前返回、未设 idle_stamp）。
- 从 idle_stamp 检查中移除 `unlikely()` 注解。
- 新增 John Stultz 的 `Acked-by`。

## 背景与问题（与 v2 一致）

commit `4b603f1551a73` 把 `rq->avg_idle` 记账从唤醒路径移入 `put_prev_task_idle()`。新 helper 丢失了原唤醒侧"仅当 `rq->idle_stamp` 非零才更新"的有效性检查，无条件计算 `rq_clock(rq) - rq->idle_stamp`；若 `idle_stamp == 0` 则把 `rq_clock(rq)` 当采样值，立即把 `rq->avg_idle` 推到钳位上限。可被 `find_proxy_task()`、force-idling 等未设 idle_stamp 即切到 idle 的路径触发。

Fixes `4b603f1551a73`。作者强调这是早期更宽方案的窄化变体：保留 `idle_stamp` 守卫，但不从 `set_next_task_idle()` 给 idle 入口打戳，避免 forced/proxy idle 计数问题。hackbench 负载下确认可被 `idle_stamp == 0` 触达，且相比 v7.2-rc5 mainline 无实质回归。已获 K Prateek Nayak `Reviewed-by` 与 John Stultz `Acked-by`。

## 状态

v3，已获 Reviewed-by + Acked-by，处于评审阶段。同日另有 tip 合入的 sched/fair 系列与此无关。

## 参考链接

- 本日 v3：uid 27672
- 前序分析：sched-20260807-019-sched-core-skip-avg-idle-no-idle-stamp
