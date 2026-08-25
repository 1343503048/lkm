# sched: use kfree_nolock() instead of kfree_rcu()

## 概述

Vlastimil Babka 的系列（RFC 5/5，本批仅见到第 5 片及 Re）将 `kfree_rcu()` 替换为新的 `kfree_nolock()`，用于调度相关路径中不能持锁/不能睡眠的释放场景。

## 背景

在调度核心（sched/core）与 perf 等路径中，某些对象的释放发生在 RCU 读侧临界区或不可睡眠上下文，传统上借助 `kfree_rcu()` 延迟到宽限期后释放。新引入的 `kfree_nolock()` 提供在禁止睡眠/禁止锁场景下的替代释放原语，可更即时地回收而不依赖 RCU 宽限期。

## 变更

在本批所见 5/5 中，将相关 `kfree_rcu()` 调用替换为 `kfree_nolock()`，减少 RCU 回调延迟。

## 状态

以 RFC 形式发布，处于早期讨论阶段；同系列其余 1-4/5 未在 8/7 候选中出现（可能已于前一日发送）。

## 参考链接

- 本批邮件：uid 27002 / 27200

---
subject: "perf/core: 用 kfree_nolock() 替代 kfree_rcu()（调度上下文释放）"
date: 2026-08-07
series: "perf-core-kfree-nolock"
version: "v1"
status: "in-review"
tags: [perf, sched/core]
related_articles: []
submitter: "Vlastimil Babka (SUSE)"
emails:
  - uid: 27002
    subject: "[PATCH RFC 5/5] sched: use kfree_nolock() instead of kfree_rcu()"
  - uid: 27200
    subject: "Re: [PATCH RFC 5/5] sched: use kfree_nolock() instead of kfree_rcu()"
---
