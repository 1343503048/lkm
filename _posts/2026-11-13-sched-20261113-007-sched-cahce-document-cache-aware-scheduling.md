---
id: sched-20261113-007
subject: 'sched/cahce: Document cache aware scheduling'
date: 2026-11-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <cover.1794507151.git.tim.c.chen@linux.intel.com>
lore_url: https://lore.kernel.org/all/cover.1794507151.git.tim.c.chen@linux.intel.com/
authors:
- Tim Chen
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <cover.1794507151.git.tim.c.chen@linux.intel.com>
  date: 2026-11-13
  summary: 新增 sched-cache.rst 文档 + 修正 can_migrate_llc() 决策矩阵注释
  review_outcome: 刚发出，暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: 等待 doc / sched 维护者评审
contribution_opportunities:
- kind: review
  description: 对照实现校验 sched-cache.rst 描述准确性
- kind: testing
  description: 按文档调优指导验证 debugfs 可调项行为
generated_at: '2026-11-14T01:30:00'
source_email_count: 3
related_articles: []
tags:
- load_balance
- numa_balancing
- topology
title: 'sched/cahce: Document cache aware scheduling'
layout: article
---

## TL;DR
Tim Chen（Intel）发两补丁系列：为 cache aware scheduling（`CONFIG_SCHED_CACHE`）补文档（新增 `Documentation/scheduler/sched-cache.rst`，与 `sched-energy.rst` 同风格），并修正 `can_migrate_llc()` 上方注释里的迁移决策矩阵（若干单元格与默认阈值下函数实际计算结果不符，且改用 45% 而非 40% 以体现 imb_pct 迟滞）。注释修复是纯注释改动、打 stable 标签。cover 标题原文有拼写笔误 "cahce"。

## 背景与问题
`CONFIG_SCHED_CACHE`（cache aware scheduling）此前缺少官方文档。系列为它补充与 `sched-energy.rst` 同风格的操作原理说明、debugfs 调参项与调优指导。同时 `kernel/sched/fair.c` 里 `can_migrate_llc()` 上方的迁移决策矩阵注释中多个单元格与默认阈值下函数实际计算不一致，需修正。

## 技术方案
- patch 1 `Documentation/scheduler: Add cache aware scheduling documentation`：新增 `Documentation/scheduler/sched-cache.rst`（554 行），解释调度器工作原理、描述 debugfs 可调项并给出调优指导，`index.rst` 加一条目。
- patch 2 `sched/cache: Fix decision matrix comment above can_migrate_llc()`：修正示例表格，改 45% 替代 40% 以同时体现 imb_pct 迟滞；纯注释改动，打 stable 使注释与 v7.2.y / v7.3.y 代码一致。

## 版本演进与当前进展
v1 刚发出，尚无 review 意见。

## Maintainer 意见与讨论焦点
当日无回帖。文档系列通常走 sched/-tip 或 Documentation 子系统，需 doc 维护者与 sched 维护者共同过目。

## 合入评估
纯文档 + 注释修正，风险低，合入概率中等偏高；暂无阻塞项。

## 效果评估
无性能数据（纯文档与注释）。

## 我可以参与的点
- **review**：对照 `CONFIG_SCHED_CACHE` 的实际实现与 debugfs 可调项，校验 `sched-cache.rst` 描述是否准确。
- **testing**：按文档调优指导在启用 `CONFIG_SCHED_CACHE` 的平台验证可调项行为。

## 参考链接
- lore thread: https://lore.kernel.org/all/cover.1794507151.git.tim.c.chen@linux.intel.com/
