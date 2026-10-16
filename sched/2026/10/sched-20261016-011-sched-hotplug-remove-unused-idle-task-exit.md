# sched/hotplug: Remove unused idle_task_exit

## TL;DR
Srikar Dronamraju 清理 CPU hotplug 路径的遗留：commit `21641bd9a7a7` 已把 `idle_task_exit()` 原来做的事情移到调度器 hotplug 路径（`sched_force_init_mm()`），该函数变成空 stub，20 个架构的调用点已无实际作用。补丁删除这些调用点与空 stub，跨 21 个文件纯删 33 行，无功能变化。

## 背景与问题
`idle_task_exit()` 原在 CPU 下线时做些收尾工作；commit `21641bd9a7a7 ("lazy tlb: fix hotplug exit race with MMU_LAZY_TLB_SHOOTDOWN")` 已把该处理移入调度器 CPU hotplug 路径（用 `sched_force_init_mm()`），使 `idle_task_exit()` 成为空 stub，各架构的调用点不再有任何效果，属于遗留死代码。

## 技术方案
单补丁（21 files changed, 33 deletions）：删除 arch/arm、arm64、csky、loongarch、mips、parisc、powerpc、riscv、s390、sh、sparc、x86、xtensa 等 20 个架构里 `arch_cpu_idle_dead()`/`cpu_die()` 等路径中对 `idle_task_exit()` 的调用，以及 `include/linux/sched/hotplug.h` 里的空 stub 声明。

## 版本演进与当前进展
v1 刚发出（<20261016095711.1364609-1-srikar@linux.ibm.com>），暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者表态。跨 20 个架构的删减本身机械，但需各架构维护者确认无遗留语义。

## 合入评估
*likelihood=high*。纯死代码清理、无功能变化，风险低；但跨多架构，仍需相关维护者确认。*blocking_issues*：暂无 review。*next_action*：等各架构/调度维护者 review 后收取。

## 效果评估
无性能/行为变化（纯删除）。无量化数据。

## 我可以参与的点
- *review*：核对各架构调用点删除后无剩余对空 stub 的引用。

## 参考链接
- patch：https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/

---
id: sched-20261016-011
date: 2026-10-16
subject: "sched/hotplug: Remove unused idle_task_exit"
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: "<20261016095711.1364609-1-srikar@linux.ibm.com>"
lore_url: "https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/"
authors: ["Srikar Dronamraju"]
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261016095711.1364609-1-srikar@linux.ibm.com>"
    date: 2026-10-16
    summary: "删除 20 个架构对 idle_task_exit() 的调用与空 stub"
    review_outcome: "暂无 review"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: ["跨 20 个架构，暂无 review"]
  next_action: "等各架构/调度维护者 review 后收取"
contribution_opportunities:
  - kind: review
    description: "核对各架构调用点删除后无剩余对空 stub 的引用"
generated_at: "2026-10-17T01:30:00"
source_email_count: 1
related_articles: []
tags: [cfs]
---