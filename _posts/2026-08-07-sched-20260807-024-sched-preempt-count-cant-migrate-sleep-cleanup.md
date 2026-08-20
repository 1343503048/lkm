---
date: 2026-08-07
series: sched-preempt-count-cant-migrate-sleep
version: v5
status: in-review
tags:
- preempt
- sched/core
related_articles: []
submitter: Boqun Feng
emails:
- uid: 26237
  subject: '[PATCH v5 09/18] sched: avoid signed comparison of preempt_count in __cant_migrate()'
- uid: 26240
  subject: '[PATCH v5 10/18] sched: remove the unused preempt offset parameter of
    __cant_sleep()'
title: 'sched: 清理 preempt_count 的 __cant_migrate/__cant_sleep 参数'
layout: article
---

## 概述

Boqun Feng 的较大系列（v5，共 18 片）中的两片，清理 `preempt_count` 相关的 `__cant_migrate()` 与 `__cant_sleep()` 实现。

## 变更内容

- **09/18**：在 `__cant_migrate()` 中避免对 `preempt_count` 的有符号比较（修正符号相关潜在判断错误）。
- **10/18**：移除 `__cant_sleep()` 中未使用的 preempt offset 参数，简化接口。

## 状态

v5 大系列的一部分（仅本批见到 9/18 与 10/18），处于评审阶段，其余片可能于其他日期发送。

## 参考链接

- 邮件：uid 26237 / 26240
