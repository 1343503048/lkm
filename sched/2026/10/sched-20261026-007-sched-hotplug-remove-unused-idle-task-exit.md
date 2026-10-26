# sched/hotplug: Remove unused idle_task_exit

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261016-011：Srikar Dronamraju 清理 CPU hotplug 遗留——`idle_task_exit()` 原工作已移入调度器 hotplug 路径（`sched_force_init_mm()`），函数成空 stub，20 个架构调用点已无作用；补丁跨 21 文件纯删 33 行。v1 发出暂无 review。
- sched-20261023-011：Frederic Weisbecker 给出 *Reviewed-by*，合入概率上升。
- sched-20261024-011：Peter Zijlstra 表态「Excellent; less is more and all that. Shall I take this through the scheduler tree?」——维护者主动提出经 scheduler 树收取，系列即将合入。
- sched-20261026-007（今天）：Frederic Weisbecker 回 Peter「Yes please :-)」确认走 scheduler 树；Jinjie Ruan（华为）补 *Reviewed-by*。系列只剩 Peter 实际收取。

## 背景与问题
（承接 20261016-011）`idle_task_exit()` 原在 CPU 下线时收尾；commit `21641bd9a7a7`（"lazy tlb: fix hotplug exit race with MMU_LAZY_TLB_SHOOTDOWN"）已把处理移入调度器 hotplug 路径（`sched_force_init_mm()`），使该函数成为空 stub、各架构调用点不再有效果，属遗留死代码。今日无新背景，为收取路径确认。

## 技术方案
（承接 20261016-011）单补丁（21 files changed, 33 deletions）：删除 arch/arm、arm64、csky、loongarch、mips、parisc、powerpc、riscv、s390、sh、sparc、x86、xtensa 等 20 个架构 `arch_cpu_idle_dead()`/`cpu_die()` 等处对 `idle_task_exit()` 的调用，以及 `include/linux/sched/hotplug.h` 的空 stub 声明。今日无代码变更，仅新增收取确认与 review 背书。

## 版本演进与当前进展
*current_version: v1*（`<20261016095711.1364609-1-srikar@linux.ibm.com>`）。当日无新版本，进展为 Frederic 确认走 scheduler 树 + Jinjie Ruan Reviewed-by。

## Maintainer 意见与讨论焦点
- **Frederic Weisbecker**：回应 Peter 的「Shall I take this through the scheduler tree?」——「Yes please :-)」，确认经 scheduler 树收取。
- **Peter Zijlstra**（承接 20261024-011）：主动提出经 scheduler 树收取。
- **Jinjie Ruan**（华为）：*Reviewed-by*。

无分歧、无 NAK，各方口径一致。

## 合入评估
*likelihood=high*。纯死代码清理、无功能变化、风险低；已获 Frederic + Jinjie Reviewed-by，Peter 主动提出并经 Frederic 确认走 scheduler 树。*blocking_issues*：无实质阻塞，待 Peter 实际收取。*next_action*：Peter 经 scheduler 树收取进 sched/core。

## 效果评估
无性能/行为变化（纯删除），无量化数据。

## 我可以参与的点
- *kind: review*：系列已近合入，可在自家分支回合时核对各架构调用点删除后无残余对空 stub 的引用。

## 参考链接
- patch: https://lore.kernel.org/all/20261016095711.1364609-1-srikar@linux.ibm.com/
- Frederic 今日回帖: https://lore.kernel.org/all/at5OxorR-UUIxlIe@pavilion.home/
- Jinjie Ruan Reviewed-by: https://lore.kernel.org/all/02118069-9360-4055-bc61-2ee2dd3486c9@huawei.com/
- 前文: sched-20261024-011 / sched-20261023-011 / sched-20261016-011

---
id: sched-20261026-007
date: 2026-10-26
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
    review_outcome: 'Frederic/Jinjie Reviewed-by；Peter 主动提出并经 Frederic 确认走 scheduler 树'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 'Peter 经 scheduler 树收取进 sched/core'
contribution_opportunities:
  - kind: review
    description: '自家分支回合时核对各架构删除后无残余空 stub 引用'
generated_at: '2026-10-27T01:00:00'
source_email_count: 2
related_articles:
  - sched-20261016-011
  - sched-20261023-011
  - sched-20261024-011
tags:
  - idle
---