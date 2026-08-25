---
id: sched-20260821-011
date: 2026-08-21
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260821075728.273004-1-gonglinkai@kylinos.cn>
lore_url: https://lore.kernel.org/lkml/20260821075728.273004-1-gonglinkai@kylinos.cn/
authors:
- Linkai Gong
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260821075728.273004-1-gonglinkai@kylinos.cn>
  date: 2026-08-21
  summary: 修复 dt_idle_genpd kfree 释放非分配起始地址的问题
  review_outcome: 暂无 review 意见
upstream_commit: null
fixes_commit: 9d976d6721df
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 review
contribution_opportunities: []
generated_at: '2026-08-21T10:00:00'
source_email_count: 1
related_articles: []
tags:
- cpuidle
- memory_safety
title: '`dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()`
  偏移）'
layout: article
---

## TL;DR

`dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移），`kfree()` 时触发内存错误。Linkai Gong 的修复改为直接 `kstrdup(kbasename(...))` 复制基名字符串。

## 背景与问题

`dt_idle_pd_alloc()` 先 `kasprintf(GFP_KERNEL, "%pOF", np)` 分配完整节点路径，然后 `pd->name = kbasename(pd->name)` 将指针偏移到路径末尾的基名部分。释放时 `kfree(pd->name)` 释放的不是分配起始地址，导致内存错误。

Fixes 标签指向 `9d976d6721df ("cpuidle: Factor-out power domain related code from PSCI domain driver")`。

## 技术方案

将 `pd->name` 的赋值改为 `kstrdup(kbasename(of_node_full_name(np)), GFP_KERNEL)`，直接复制基名字符串，这样 `kfree()` 释放的就是分配起始地址。同时删除多余的 `kbasename()` 调用。

## 版本演进与当前进展

v1 刚发出，暂无 review 意见。

## Maintainer 意见与讨论焦点

暂无 review 意见。

## 合入评估

- **likelihood**: high
- **blocking_issues**: 无
- **next_action**: 等待 review

典型的内存安全修复，方向明确。

## 效果评估

修复内存错误，无性能数据。

## 我可以参与的点

当前阶段暂无明显参与空间，补丁简单明确。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260821075728.273004-1-gonglinkai@kylinos.cn/
- tip-bot commit: 未获取到
- stable backport: 未获取到
