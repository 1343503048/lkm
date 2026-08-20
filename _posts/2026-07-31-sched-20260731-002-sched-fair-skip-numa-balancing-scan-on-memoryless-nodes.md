---
id: sched-20260731-002
date: 2026-07-31
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: <20260730175151.3855700-1-pohaosu@google.com>
lore_url: https://lore.kernel.org/lkml/20260730175151.3855700-1-pohaosu@google.com
authors:
- Phineas Su
maintainers_involved:
- Peter Zijlstra
- Bharata B Rao
current_version: v1
patch_series:
- version: v1
  msgid: <20260730175151.3855700-1-pohaosu@google.com>
  date: 2026-07-30
  summary: 在无内存 NUMA 节点上跳过 NUMA balancing 扫描，避免 ~78% sys CPU 开销
  review_outcome: PeterZ 认为不应完全禁用扫描，应确保页面在距离最近的节点上；Bharata 建议在 mm 侧的 numa_migrate_check()
    中抑制迁移而非跳过 task_numa_work()
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - PeterZ 和 Bharata 都不同意当前方案，认为不应完全跳过 task_numa_work()
  - 需要重新设计方案
  next_action: 作者需要回应 PeterZ 和 Bharata 的反馈，可能需要改为在 numa_migrate_check() 中处理而非跳过整个扫描
contribution_opportunities:
- kind: discussion
  description: 无内存 NUMA 节点的场景下，最佳处理方式存在分歧，可以参与讨论提出方案
generated_at: '2026-07-31T16:30:00'
source_email_count: 3
related_articles: []
tags:
- cfs
- numa_balancing
- load_balance
title: 'sched/fair: Skip NUMA balancing scan on memoryless nodes'
layout: article
---

## TL;DR

Phineas Su (Google) 发现无内存 NUMA 节点上自动 NUMA balancing 导致 ~78% sys CPU 开销和持续 page fault 风暴。补丁在 task_tick_numa() 和 task_numa_work() 中增加 N_MEMORY 检查跳过扫描。但 PeterZ 和 Bharata 均不同意完全跳过扫描的方案，认为应在 mm 侧抑制迁移而非跳过整个 VMA 扫描。合入可能性低，需要重新设计。

## 背景与问题

在具有无内存 NUMA 节点的系统上（如通过 memory hiding 创建的 CPU-only 节点、未安装内存的 socket 拓扑），运行在这些 CPU 上的任务会导致自动 NUMA balancing（kernel.numa_balancing=1）反复调度 task_numa_work()。

当 task_numa_work() 执行时，它会 unmap VMA（PROT_NONE）以引发 NUMA hinting fault。fault 处理尝试页面迁移（migrate_misplaced_folio()），但因为节点没有托管内存（N_MEMORY 为 false），页面分配持续失败（TNF_MIGRATE_FAIL），而 task_tick_numa() 仍反复重新调度 VMA 扫描。结果：

- **%sys CPU 使用率飙升至约 78%**
- 持续的 page fault 风暴，无任何 NUMA 放置收益

## 技术方案

补丁在两个位置增加 `node_state(task_node(...), N_MEMORY)` 检查：

1. **task_tick_numa()**：CPU 上无内存节点的任务不调度 numa_work 回调
2. **task_numa_work()**：作为安全网，如果任务在 numa_work 已入队后迁移到无内存节点，立即中止 VMA 扫描

修改仅 6 行代码，在 `kernel/sched/fair.c` 中。

## 版本演进与当前进展

- **v1**（2026-07-30）：刚发出即收到 PeterZ 和 Bharata 的反馈，方向存在分歧

## Maintainer 意见与讨论焦点

**Peter Zijlstra** 明确表示不同意完全禁用扫描：

> "Rather than fully disabling, I would argue the right thing is to ensure the pages are nearest the node the task runs on."

PeterZ 认为即使当前节点无内存，也不应跳过扫描——应该确保页面在距离当前节点最近（distance 最小）的节点上。完全不迁移可能导致内存停留在距离最远的节点上，同样不是最优。

**Bharata B Rao (AMD)** 建议：

- task_numa_work() 还负责 VMA 扫描，抑制它可能有问题——任务可能迁移到有 CPU 和内存的节点，hinting fault 可以帮助确定这一点
- 应该在 mm 侧的 `numa_migrate_check()` 中抑制向 !N_MEMORY 节点的迁移，而非跳过整个 task_numa_work()
- `task_numa_fault()` 在失败路径上可以将任务迁移到热页面所在的 CPU 节点，而非尝试将页面迁移到无内存的任务所在节点

## 合入评估

- **likelihood: low** — 两位资深维护者都不同意当前方案方向
- **blocking_issues**: PeterZ 和 Bharata 都认为不应跳过 task_numa_work()，需要在 mm 侧处理
- **next_action**: 作者需要重新考虑方案，可能改为在 `numa_migrate_check()` 中增加 N_MEMORY 检查，同时保留 VMA 扫描功能

## 效果评估

作者报告修复前 %sys CPU 使用率飙升至约 78%，修复后消除。但维护者认为方案过于激进，可能引入新的次优问题（内存停留在远距离节点）。

## 我可以参与的点

- **参与讨论**：无内存 NUMA 节点场景下的最佳处理方式存在分歧，如果有此类硬件环境的测试数据，可以帮助评估不同方案的实际影响
- **提出替代方案**：可以分析在 `numa_migrate_check()` 中增加 N_MEMORY 检查的可行性，作为 Bharata 建议的具体实现

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260730175151.3855700-1-pohaosu@google.com
