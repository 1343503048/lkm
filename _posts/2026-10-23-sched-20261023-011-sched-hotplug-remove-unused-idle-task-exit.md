---
id: sched-20261023-011
date: 2026-10-23
subject: 'sched/hotplug: Remove unused idle_task_exit'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: <20261016095711.1364609-1-srikar@linux.ibm.com>
lore_url: https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/
authors:
- Srikar Dronamraju
maintainers_involved:
- Frederic Weisbecker
current_version: v1
patch_series:
- version: v1
  msgid: <20261016095711.1364609-1-srikar@linux.ibm.com>
  date: 2026-10-16
  summary: 删除 20 架构的 idle_task_exit 调用点与空 stub
  review_outcome: Frederic Weisbecker Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 跨多架构仍需相关维护者最终收取
  next_action: 等 sched 维护者收取
contribution_opportunities:
- kind: review
  description: 核对各架构删除后无剩余对空 stub 的引用
generated_at: '2026-10-24T09:10:00'
source_email_count: 1
related_articles:
- sched-20261016-011
tags:
- idle
title: 'sched/hotplug: Remove unused idle_task_exit'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-011-sched-hotplug-remove-unused-idle-task-exit.html">sched-20261016-011</a>：Srikar Dronamraju 清理 CPU hotplug 路径的遗留——commit `21641bd9a7a7` 已把 `idle_task_exit()` 原来做的事情移到调度器 hotplug 路径（`sched_force_init_mm()`），该函数变成空 stub，20 个架构的调用点已无实际作用；补丁删除这些调用点与空 stub，跨 21 个文件纯删 33 行、无功能变化。当日 v1 发出、暂无 review。
- <a class="article-ref" href="/lkm/2026/10/23/sched-20261023-011-sched-hotplug-remove-unused-idle-task-exit.html">sched-20261023-011</a>（今天）：Frederic Weisbecker 给出 *Reviewed-by*。纯死代码清理获首个（且核心相关）维护者背书，合入概率进一步上升。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-011-sched-hotplug-remove-unused-idle-task-exit.html">sched-20261016-011</a>）`idle_task_exit()` 原在 CPU 下线时做些收尾工作；commit `21641bd9a7a7`（"lazy tlb: fix hotplug exit race with MMU_LAZY_TLB_SHOOTDOWN"）已把该处理移入调度器 CPU hotplug 路径（用 `sched_force_init_mm()`），使 `idle_task_exit()` 成为空 stub，各架构调用点不再有任何效果，属于遗留死代码。今日背景无新增。

## 技术方案
（承接 <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-011-sched-hotplug-remove-unused-idle-task-exit.html">sched-20261016-011</a>）单补丁（21 files changed, 33 deletions）：删除 arch/arm、arm64、csky、loongarch、mips、parisc、powerpc、riscv、s390、sh、sparc、x86、xtensa 等 20 个架构里 `arch_cpu_idle_dead()`/`cpu_die()` 等路径中对 `idle_task_exit()` 的调用，以及 `include/linux/sched/hotplug.h` 里的空 stub 声明。今日无新代码，仅新增 review 背书。

## 版本演进与当前进展
*current_version: v1*（`<20261016095711.1364609-1-srikar@linux.ibm.com>`）。当日无新版本，进展为获得 Frederic Weisbecker 的 Reviewed-by。

## Maintainer 意见与讨论焦点
Frederic Weisbecker（此前「lazy tlb hotplug」相关改动的主要维护者）给出 *Reviewed-by*。无异议或分歧。跨 20 个架构的删减本身机械，仍需各架构维护者确认无遗留语义。

## 合入评估
*likelihood=high*。纯死代码清理、无功能变化、风险低；已获核心相关维护者 Frederic 的 Reviewed-by。*blocking_issues*：跨多架构，仍需相关架构维护者（或 sched 维护者）最终收取。*next_action*：等 Peter/sched 维护者收取进 sched/core 或直接由 Frederic 经相应树合入。

## 效果评估
无性能/行为变化（纯删除）。无量化数据。

## 我可以参与的点
- *kind: review*：核对各架构调用点删除后无剩余对空 stub 的引用。

## 参考链接
- patch: https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/
- Frederic 回帖: https://lore.kernel.org/all/attjv8zOftf9Hlqe@localhost.localdomain/
- 前文: <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-011-sched-hotplug-remove-unused-idle-task-exit.html">sched-20261016-011</a>
