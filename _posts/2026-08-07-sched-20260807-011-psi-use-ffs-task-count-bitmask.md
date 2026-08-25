---
subject: 'psi: 用 __ffs() 遍历 task count 位图'
date: 2026-08-07
series: psi-use-ffs
version: v2
status: in-review
tags:
- psi
- perf
related_articles: []
submitter: 社区
emails:
- uid: 26540
  subject: '[PATCH v2] psi: use __ffs() to walk task count bitmasks in psi_group_cpu()'
title: 'sched/psi: use __ffs() to walk task-count bitmasks in psi_group_change()'
layout: article
---

## 概述

将 PSI（`psi_group_cpu()`）中对 task count 位图的遍历从线性扫描改为 `__ffs()` 跳跃式查找，跳过为 0 的位以提升效率。

## 变更内容

在 `psi_group_cpu()` 统计各任务状态计数时，原先逐位判断哪些任务状态位被置位。改用 `__ffs()` 直接从最低置位位开始遍历，减少无效迭代，对高 CPU 数/多任务场景的 PSI 采样开销有改善。

## 状态

v2 迭代，处于评审阶段。

## 参考链接

- 邮件：uid 26540
