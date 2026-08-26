---
title: "[Question] 用户态限流 + 「Combine detach into dequeue」导致 guest 启动挂起（讨论继续）"
date: 2026-08-26
tags: [sched/fair, crash, regression]
series: "combine detach dequeue guest boot hang"
type: bug
severity: high
status: under_review
related_articles: ["sched-20260825-009-question-combine-detach-dequeue-guest-hang.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-25 的文章）

报告者反馈：在开启用户态限流（cgroup cpu 限流）场景下，配合主线提交
`sched/fair: Combine detach into dequeue when migrating task`，会导致 **guest（虚拟机）
启动挂起（boot hang）**。

本期（Re: UID 58771、59025）为该问题的讨论继续，尚未看到明确的因果确认、最小复现
脚本或修复补丁；焦点仍在「该提交是否为此回归的根因」以及「限流 + 迁移时序」的交互上。

## 触发条件

- 配置：对 guest 相关 cgroup 施加 userspace/CPU 限流（throttling）。
- 内核：含 `Combine detach into dequeue when migrating task` 的较新主线。
- 现象：guest 启动过程中挂起，无继续进展。

## 状态与讨论

- 当前状态：**under_review / 问题报告阶段**（以 `[Question]` 形式推进）。
- 严重度：**high**（guest 无法启动）。
- 仍需确认：是否主线可稳定复现、是否目标提交因果、有无修复方向。

## 关联

- 08-25 009 同主题问题报告
- 009（同日）sched/fair reduce repeated work in enqueue path（同属 enqueue/fair 活跃话题）
