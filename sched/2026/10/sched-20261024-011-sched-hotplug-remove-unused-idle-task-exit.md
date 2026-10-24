# sched/hotplug: Remove unused idle_task_exit

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261016-011：Srikar Dronamraju 清理 CPU hotplug 遗留——`idle_task_exit()` 原工作已移入调度器 hotplug 路径，函数成空 stub，20 个架构调用点已无作用；补丁跨 21 文件纯删 33 行。v1 发出暂无 review。
- sched-20261023-011：Frederic Weisbecker 给出 *Reviewed-by*，合入概率上升。
- sched-20261024-011（今天）：Peter Zijlstra 表态「Excellent; less is more and all that. Shall I take this through the scheduler tree?」——维护者主动提出经 scheduler 树收取，系列即将合入。

## 背景与问题
（承接 20261016-011）`idle_task_exit()` 原在 CPU 下线时收尾；commit `21641bd9a7a7` 已把处理移入调度器 hotplug 路径（`sched_force_init_mm()`），使该函数成为空 stub、各架构调用点不再有效果，属遗留死代码。今日无新背景，为收取意向确认。

## 技术方案
（承接 20261016-011）单补丁（21 files changed, 33 deletions）：删除 arch/arm、arm64、csky、loongarch、mips、parisc、powerpc、riscv、s390、sh、sparc、x86、xtensa 等 20 个架构 `arch_cpu_idle_dead()`/`cpu_die()` 等处对 `idle_task_exit()` 的调用，以及 `include/linux/sched/hotplug.h` 的空 stub 声明。今日无新代码，仅新增维护者收取意向。

## 版本演进与当前进展
*current_version: v1*（`<20261016095711.1364609-1-srikar@linux.ibm.com>`）。当日无新版本，进展为 Peter Zijlstra 主动提出经 scheduler 树收取。

## Maintainer 意见与讨论焦点
Peter Zijlstra 今日表态「Excellent; less is more and all that. Shall I take this through the scheduler tree?」，明确愿意收取。此前 Frederic Weisbecker 已 *Reviewed-by*。无分歧，等待作者确认后收取。

## 合入评估
*likelihood=high*。纯死代码清理、无功能变化、风险低；已获 Frederic Reviewed-by，如今 Peter 主动提出经 scheduler 树收取。*blocking_issues*：待作者确认（可能补齐跨架构 Ack 后）。*next_action*：作者回应 Peter 后经 scheduler 树合入。

## 效果评估
无性能/行为变化（纯删除），无量化数据。

## 我可以参与的点
- *kind: review*：核对各架构调用点删除后无剩余对空 stub 的引用。

## 参考链接
- patch: https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/
- Peter 今日回帖: https://lore.kernel.org/all/20261023165434.GX2823843@noisy.programming.kicks-ass.net/
- 前文: sched-20261023-011 / sched-20261016-011

---
id: sched-20261024-011
date: 2026-10-24
subject: 'sched/hotplug: Remove unused idle_task_exit'
subsystem: sched
type: fix
status: under_review
severity: none
thread_root_msgid: '<20261016095711.1364609-1-srikar@linux.ibm.com>'
lore_url: 'https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/'
authors:
  - 'Srikar Dronamraju'
maintainers_involved:
  - 'Peter Zijlstra'
  - 'Frederic Weisbecker'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261016095711.1364609-1-srikar@linux.ibm.com>'
    date: 2026-10-16
    summary: '删除 20 架构的 idle_task_exit 调用点与空 stub'
    review_outcome: 'Frederic Reviewed-by；Peter 主动提出经 scheduler 树收取'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - '待作者确认（可能补齐跨架构 Ack）'
  next_action: '作者回应后经 scheduler 树合入'
contribution_opportunities:
  - kind: review
    description: '核对各架构调用点删除后无残余空 stub 引用'
generated_at: '2026-10-25T01:00:00'
source_email_count: 1
related_articles:
  - sched-20261023-011
tags:
  - idle
---