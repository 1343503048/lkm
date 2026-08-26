---
title: "sched/fair：同一任务重新选核后重启 hrtick"
date: 2026-08-26
tags: [sched/fair]
series: "restart hrtick same-task repicks"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

在 `sched/fair` 中，当发生「同一任务重新选核/重新入队（same-task repicks）」时，
既有的 hrtick（高精度抢占定时）未被正确重启，可能导致该任务在该 CPU 上多跑一段
才被抢占，影响延迟与公平性的时序保证。本期（Re: UID 58299、58412）提出在 same-task
repicks 路径上重新启动 hrtick。

## 改动内容 / 核心补丁

- 在 same-task repicks 的入队/选核完成后，重启 hrtick 定时，使抢占边界与预期一致。
- 属于 fair 类抢占时序的小幅修正。

## 状态与讨论

- 当前状态：**under_review**（以 Re: 形式推进，原始补丁未在 08-26 窗口内独立出现）。
- 合入概率 medium；影响 hrtick 用户的抢占延迟准确性。

## 关联

- 009 sched/fair：reduce repeated work in enqueue path（v2，同为 enqueue/fair 清理）
