---
subject: 'sched/cache: Fix a thread aggregation conflict when there is one runnable
  task'
id: sched-20260728-006
date: 2026-07-28
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260727121730.2148901-1-zhanxusheng1024@gmail.com>
lore_url: https://lore.kernel.org/r/20260727121730.2148901-1-zhanxusheng1024@gmail.com
authors:
- Zhan Xusheng
maintainers_involved:
- Tim Chen
current_version: v1
patch_series:
- version: v1
  msgid: <20260727121730.2148901-1-zhanxusheng1024@gmail.com>
  date: 2026-07-27
  summary: Fix thread aggregation conflict when there is one runnable task on asymmetric
    capacity systems
  review_outcome: Tim Chen 给出 Reviewed-by，建议保持 SD_ASYM_CPUCAPACITY 现有逻辑不变
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 已有 Reviewed-by，等待 maintainer apply
contribution_opportunities: []
generated_at: '2026-07-30T10:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- topology
title: 'sched/cache: Fix a thread aggregation conflict when there is one runnable
  task'
layout: article
---

## TL;DR

Zhan Xusheng 发出修复补丁，解决只有一个 runnable task 时的线程聚合冲突。Tim Chen (Intel) 已给出 Reviewed-by，并建议 `SD_ASYM_CPUCAPACITY` 相关代码保持现状。合入可能性高。

## 背景与问题

在 asymmetric capacity 系统（如 Intel 混合 CPU 的 P-core/E-core）上，当只剩一个 runnable task 时，线程聚合逻辑与 CPU capacity 选择产生冲突。

## 技术方案

修复单 runnable task 场景下的聚合冲突。Tim Chen 在 review 中特别指出：

> "SD_ASYM_CPUCAPACITY is mostly used in the hybrid CPU situations (e.g. P-core and E-core on some Intel client CPUs). For those, the difference in CPU performance is pretty significant and we likely will not get as much performance back from cache co-location vs the CPU capacity. So I think we can leave the SD_ASYM_CPUCAPACITY code as is till we come across a workload and platform that shows otherwise."

即：在混合 CPU 上，P/E core 的性能差异远大于 cache co-location 带来的收益，所以 `SD_ASYM_CPUCAPACITY` 路径不需要改动。

## 版本演进与当前进展

v1（2026-07-27）：首次发出。Tim Chen 于 7 月 28 日给出 Reviewed-by。

## Maintainer 意见与讨论焦点

- **Tim Chen**：Reviewed-by，认同修复方向，同时明确 `SD_ASYM_CPUCAPACITY` 代码不需要改动
- 无争议，无 NAK

## 合入评估

可能性高。已有 Intel 资深调度开发者 Tim Chen 的 Reviewed-by，修复范围小且方向明确。

## 效果评估

暂无具体 benchmark 数据。修复针对边缘场景（单 runnable task + asymmetric capacity），影响面有限。

## 我可以参与的点

当前阶段暂无明显参与空间。已有 Reviewed-by，预计很快合入。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260727121730.2148901-1-zhanxusheng1024@gmail.com
- tip-bot commit: 未获取到
