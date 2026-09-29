# kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)

> **subject**：`kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)`

## TL;DR

kernel test robot（0day）报出 `sched_ext: Eject the top rescue consumer on overload`（commit `bb70e4fb626b`）上的一批 sparse 地址空间（`__rcu`）告警：`rq->donor`/`->curr` 作为 `__rcu` 指针被当作非 `__rcu` 使用，告警横跨 `kernel/sched/deadline.c` 与 `kernel/sched/ext/ext.c`（标题列的 sub.c:288 是其中之一）。这是 proxy execution donor 改造遗留的 `__rcu` 标注/访问不一致，当前无人工回应。

## 背景与问题

sparse 在 arm-randconfig（clang-24 + sparse v0.6.5-rc1，W=1）下报出多处「different address spaces」告警，核心模式是把 `struct task_struct [noderef] __rcu *donor/*curr` 传给期望裸 `struct task_struct *` 的函数或与之比较。0day 把该报告关联到 commit `bb70e4fb626b`（"sched_ext: Eject the top rescue consumer on overload"），但这些告警更广泛地出现在 proxy execution 引入 `rq->donor`（`__rcu` 标注）之后、尚未全部刷的访问点上。

## 技术方案

这是静态分析告警，非补丁方案。0day 建议若以单独补丁修复，请带 `Fixes: bb70e4fb626b` 与 `Reported-by: kernel test robot <lkp@intel.com>`。示例告警（原文摘录）：

- `kernel/sched/deadline.c:3314`：expected `struct task_struct *p`，got `struct task_struct [noderef] __rcu *donor`。
- `kernel/sched/deadline.c:3578`：`__rcu *` 与非 `__rcu *` 在比较表达式里地址空间不兼容。
- `kernel/sched/ext/ext.c:391/1423/1613`：initializer 里 expected `*curr` got `[noderef] __rcu *curr`。
- `kernel/sched/ext/sub.c:288`（标题所列）。

## 版本演进与当前进展

首报（`<202609282245.GrTRG62D-lkp@intel.com>`），无后续回复。

## Maintainer 意见与讨论焦点

当日无人回复。是否修、怎么修（`rcu_dereference()` 包一层 / 调整 `__rcu` 标注）均未有人表态。

## 合入评估

*likelihood=unknown*。静态分析告警、无功能崩溃，无人工回应，是否被认领无法判断。*blocking_issues*：无回应。*next_action*：等 sched/sched_ext 维护者判断这些 `__rcu` 访问是否需要统一修复（或属已知非问题）。

## 效果评估

无性能影响；属代码卫生/静态分析告警（可能掩盖真实的 RCU lifetime 隐患）。

## 我可以参与的点

- `review`：核对这些 `rq->donor`/`rq->curr` 的 `__rcu` 访问是否与 proxy execution 的 donor 生命周期一致、是否应统一用 `rcu_dereference()`，给出修复 patch（`new_patch`）。

## 参考链接

- lore（0day 报告）: https://lore.kernel.org/all/202609282245.GrTRG62D-lkp@intel.com/

---
id: sched-20260929-021
date: '2026-09-29'
subject: 'kernel/sched/ext/sub.c:288:16: sparse: sparse: incorrect type in argument 1 (different address spaces)'
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: '<202609282245.GrTRG62D-lkp@intel.com>'
lore_url: 'https://lore.kernel.org/all/202609282245.GrTRG62D-lkp@intel.com/'
authors:
  - 'kernel test robot'
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: 'bb70e4fb626b'
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - '无人工回应'
  next_action: '等维护者判断这些 __rcu 访问是否需要统一修复'
contribution_opportunities:
  - kind: new_patch
    description: '核对 rq->donor/rq->curr 的 __rcu 访问并给统一 rcu_dereference 修复'
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles: []
tags:
  - sched_ext
  - sched_debug
---