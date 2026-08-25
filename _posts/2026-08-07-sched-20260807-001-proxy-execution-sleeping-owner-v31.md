---
subject: 'Proxy Execution: Sleeping Owner Handling (v31, resend)'
date: 2026-08-07
series: proxy-execution
version: v31
status: in-review
tags:
- proxy_execution
- sched/core
- core_sched
related_articles: []
submitter: John Stultz
emails:
- uid: 26038
  subject: '[PATCH resend v31 0/9] Sleeping Owner Handling for Proxy Execution, v31'
- uid: 26036
  subject: '[PATCH resend v31 1/9] sched/deadline: Ignore proxy exec sched deadline'
title: '[PATCH v31 0/9] Sleeping Owner Handling for Proxy Execution (v31)'
layout: article
---

## 概述

John Stultz 重新发送（resend）了 Proxy Execution 的下一大组件 —— **Sleeping Owner Handling（沉睡属主处理）** 的 v31 迭代。该工作是 proxy-exec 旅程的第 5 阶段（前序为 prep → single rq proxying → simple donor migration → optimized donor migration；后续还有 chain level balancing、proxy rwsems 等）。

因上一轮假期期间反馈少，作者主动重发以推动评审。

## 核心变更

本批除 sleeping owner handling 主体外，还纳入了若干来自社区的核心调度修复与优化：

- **Sleeping Owner Handling（主体）**：处理任务阻塞在 mutex 上、而 mutex 的属主正在睡眠的情形。此时无法提升沉睡属主，故将 waiter 去激活并挂到属主上的一个链表；属主唤醒后，在同一 rq 上激活这些 waiter，使其得以提升属主运行。
  - 该逻辑会产生 waiter 树，且树中间节点也可能被唤醒，需用额外链表以非递归方式管理级联唤醒，复杂度较高。
- Vasily Gorbik 与 K Prateek 的核心调度修复。
- Christian Loehle 的 DL 修复（`yield_task_dl()` 在 proxying 时提前返回）。
- 上一阶段遗留的 chain migration 优化。

## v31 新内容

- 纳入 Christian 的修复：proxying 时 `yield_task_dl()` 提前返回。
- 修复 K Prateek 指出的竞态：若 sleeping owner 被唤醒与 waiter 入队到该 sleeping owner 并行发生，waiter 可能卡在该 owner 上直至其再次睡眠并被唤醒。已加修复。
- 修正 Maria Yu 与 Tengfei Fan 报告的 `rq->nr_iowait` 计数失衡问题（含 reproducer）。

## 状态与展望

作者希望前序 patch 能顺利入队，但预计最后两片（复杂的 waiter 树与级联唤醒逻辑）会收到大量评审反馈。

## 参考链接

- LKML 线程 v31 0/9：见邮件 uid 26038
- 历程脉络：prep → single rq proxying → simple/optimized donor migration → **sleeping owner handling（本批）** → chain level balancing → proxy rwsems
