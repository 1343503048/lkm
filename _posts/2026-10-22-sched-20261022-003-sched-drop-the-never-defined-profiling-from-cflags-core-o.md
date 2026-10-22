---
id: sched-20261022-003
date: 2026-10-22
subject: 'sched: Drop the never-defined $(PROFILING) from CFLAGS_core.o'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261022061231.610118-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261022061231.610118-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261022061231.610118-1-sh_def@163.com>
  date: 2026-10-22
  summary: 移除未定义的 $(PROFILING)，仅保留 -fno-omit-frame-pointer
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待维护者收取
contribution_opportunities: []
generated_at: '2026-10-23T01:20:00'
source_email_count: 1
related_articles: []
tags: []
title: 'sched: Drop the never-defined $(PROFILING) from CFLAGS_core.o'
layout: article
---

## TL;DR
Hui Su 发往 sched 的单补丁清理：`kernel/sched/Makefile` 里 `CFLAGS_core.o := $(PROFILING) -fno-omit-frame-pointer` 中的 `$(PROFILING)` 从未在构建系统里定义，实际只展开为 `-fno-omit-frame-pointer`。该引用是调度器构建规则仍留在 kernel/Makefile 时代的遗留，ftrace 编译选项早已移到 `CC_FLAGS_FTRACE`（c0a80c0c27e5）并由 `KBUILD_CFLAGS` 加给所有目标。当日无回帖。

## 背景与问题
纯代码/构建清理，无实际功能痛点：`$(PROFILING)` 未定义导致其空展开，仅让 Makefile 显得有「分析器开关」的假象。历史遗留——调度器对象曾内联在 kernel/Makefile 里编译，后来 ftrace 的编译器选项统一由 `CC_FLAGS_FTRACE` 承载。

## 技术方案
单补丁（`kernel/sched/Makefile`，+1/-1）：把 `CFLAGS_core.o := $(PROFILING) -fno-omit-frame-pointer` 简化为 `CFLAGS_core.o := -fno-omit-frame-pointer`，行为不变（`$(PROFILING)` 本就空展开）。

## 版本演进与当前进展
*current_version: v1*（`<20261022061231.610118-1-sh_def@163.com>`）。当日无回帖。

## Maintainer 意见与讨论焦点
未获取到当日维护者或评审意见。

## 合入评估
*likelihood=medium*。属无风险的一行构建清理，行为等价；但当日尚无任何回帖，*blocking_issues*：无；*next_action*：等维护者收取。

## 效果评估
构建清理，无运行时性能影响。

## 我可以参与的点
当前阶段暂无明显参与空间，可持续观察后续版本。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261022061231.610118-1-sh_def@163.com/
