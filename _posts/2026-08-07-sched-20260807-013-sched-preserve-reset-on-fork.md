---
subject: 'sched: 并发 sched_setparam 下保留 reset-on-fork'
date: 2026-08-07
series: sched-preserve-reset-on-fork
version: v1
status: in-review
tags:
- sched/core
- cgroup
related_articles: []
submitter: Andrea Righi
emails:
- uid: 26398
  subject: '[PATCH] sched: preserve reset-on-fork across concurrent sched_setparam()'
title: sched preserve reset on fork
layout: article
---

## 概述

Andrea Righi 修复并发 `sched_setparam()` 调用会破坏 `SCHED_RESET_ON_FORK` 标志的问题。

## 问题

`SCHED_RESET_ON_FORK` 是 `sched_setattr()` 的一个标志：fork 出的子进程在 exec/setattrs 前重置调度策略为 DEFAULT。当多个线程/进程并发调用 `sched_setparam()` 修改同一任务（或父子）的调度参数时，在缺乏正确保护的路径中 `reset-on-fork` 位可能被覆盖丢失，导致 fork 后策略未按预期重置。

## 变更

在 `sched_setparam()` 的处理中正确保留 `reset-on-fork` 标志，避免并发更新将其清除。

## 状态

v1，处于评审阶段。

## 参考链接

- 邮件：uid 26398
