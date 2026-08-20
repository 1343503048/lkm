---
subject: 'sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新'
date: 2026-08-07
series: sched-core-skip-avg-idle
version: v2
status: in-review
tags:
- sched/core
- idle
related_articles: []
submitter: Shubhang Kaushik (Ampere)
emails:
- uid: 26000
  subject: '[PATCH v2] sched/core: Skip rq->avg_idle update without a valid idle stamp'
- uid: 25889
  subject: 'Re: [PATCH v2] sched/core: Skip rq->avg_idle update without a valid idle
    stamp'
- uid: 25908
  subject: 'Re: [PATCH v2] sched/core: Skip rq->avg_idle update without a valid idle
    stamp'
title: sched core skip avg idle no idle stamp
layout: article
---

## 概述

Shubhang Kaushik（Ampere）修复 `update_rq_avg_idle()` 在无有效 idle 间隔时错误地驱动 `rq->avg_idle` 到钳位值的问题。

## 问题

旧 accounting 仅在 `rq->idle_stamp` 非零时更新 `rq->avg_idle`；新的 helper 丢失了该有效性检查，无条件计算 `rq_clock(rq) - rq->idle_stamp`。若 `rq->idle_stamp == 0`，则把 `rq_clock(rq)` 当成采样值——这不是有效 idle 时长，可立即把 `rq->avg_idle` 推到钳位上限。

该情形可在调度经未通过 `newidle_balance()` 设置 `rq->idle_stamp` 的路径切到 idle 任务时触发，例如 `find_proxy_task()` 或 force-idling 期间。

## 修复

在 `update_rq_avg_idle()` 中恢复 `idle_stamp` 有效性检查，无测量到的 idle 间隔时跳过 `rq->avg_idle` 更新。Fixes `4b603f1551a73`（"sched: Update rq->avg_idle when a task is moved to an idle CPU"）。已获 K Prateek Nayak `Reviewed-by`。

作者明确这是早期更宽方案的窄化变体：保留 `rq->idle_stamp` 守卫，但**不**从 `set_next_task_idle()` 给 idle 入口打戳，以保留既有 newidle accounting 模型、避免 forced/proxy idle 计数问题。hackbench 负载下确认 `update_rq_avg_idle()` 可被 `idle_stamp == 0` 触达；hackbench 相比 v7.2-rc5 mainline 无实质回归。

## 状态

v2，已获 Reviewed-by，处于评审阶段。

## 参考链接

- 邮件：uid 26000 / 25889 / 25908
