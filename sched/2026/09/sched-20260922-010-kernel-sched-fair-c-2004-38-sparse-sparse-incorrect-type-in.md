# kernel/sched/fair.c:2004:38: sparse: sparse: incorrect type in initializer (different address spaces)

## TL;DR
kernel test robot 的 sparse 报告：`kernel/sched/fair.c` 中 `update_curr_fair()`（`for_each_sched_entity` 展开处）及 `sched.h` 的 `task_dl_entity`/RT 相关比较，把标注为 `__rcu` 的 `struct task_struct` 与普通指针混用，触发 `incorrect type in initializer / incompatible types in comparison expression (different address spaces)`。针对已合入 commit `85570f10a4c6`（"sched/eevdf: Move to a single runqueue"，约 3 个月前）。属低严重度的 `__rcu` 类型标注缺失，暂无修复者认领。

## 背景与问题
sparse（v0.6.5-rc1）在 alpha-randconfig W=1 构建下报错：`kernel/sched/fair.c:1335:49` 等位置初始化 `struct task_struct *running` 时，期望普通 `struct task_struct *` 却得到 `struct task_struct [noderef] __rcu *curr`；`kernel/sched/sched.h:2454/2465` 的比较表达式中也把 `__rcu` 指针与普通指针比较。根因是把 rq 上 `__rcu` 标注的 `curr` 直接用（未 `rcu_dereference` 或未在访问时刻析出 `__rcu` 属性），经 `for_each_sched_entity` 宏传到普通指针语境。sparse 报告的修复建议提示 `Fixes: 85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`。

## 技术方案
本日仅为静态分析报告，无修复补丁。修复方向通常是对 `sched_entity`/`task_struct *curr` 的访问点做 `rcu_dereference()` 或调整 `__rcu` 标注，或在宏展开路径上析出 `__rcu` 属性。

## 版本演进与当前进展
sparse 报告（`<202609221957.fJCjN9uZ-lkp@intel.com>`）当日发出，无开发者回复，无修复补丁。

## Maintainer 意见与讨论焦点
当日无维护者表态。此类 sparse `__rcu` 噪音通常由对应代码 owner 认领后补齐标注或加 `rcu_dereference`。

## 合入评估
*likelihood=low*。无修复者认领，非运行时 bug（仅 sparse 类型检查），优先级低。*blocking_issues*：无修复者、非功能性、需定位宏展开路径上的 `__rcu` 访问。*next_action*：sched/fair maintainer 或有兴趣者补齐 `__rcu` 标注/`rcu_dereference` 并提交修复。

## 效果评估
无运行时影响；仅为 W=1 sparse 静态检查的 address-space 类型告警。

## 我可以参与的点
- **new_patch**：为 `update_curr_fair()` 与 `sched.h` 中 `curr` 的比较/初始化处补齐 `rcu_dereference` 或 `__rcu` 标注，提交修复（这是直接可做的小修复）。
- **testing**：本地跑 `make C=2` sparse 复现并验证修复。

## 参考链接
- lore report: https://lore.kernel.org/all/202609221957.fJCjN9uZ-lkp@intel.com/

---
id: sched-20260922-010
date: '2026-09-22'
subject: 'kernel/sched/fair.c:2004:38: sparse: sparse: incorrect type in initializer (different address spaces)'
subsystem: sched
type: bug
status: stalled
severity: low
thread_root_msgid: '<202609221957.fJCjN9uZ-lkp@intel.com>'
lore_url: 'https://lore.kernel.org/all/202609221957.fJCjN9uZ-lkp@intel.com/'
authors:
  - 'kernel test robot'
maintainers_involved: []
current_version: v1
patch_series:
  - version: v1
    msgid: '<202609221957.fJCjN9uZ-lkp@intel.com>'
    date: '2026-09-22'
    summary: 'sparse 报告 fair.c/sched.h 的 __rcu 标注缺失（different address spaces）'
    review_outcome: '无回应'
upstream_commit: null
fixes_commit: '85570f10a4c6'
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - '无修复者认领'
    - '非功能性，优先级低'
  next_action: '补齐 __rcu 标注/rcu_dereference 并提交修复'
contribution_opportunities:
  - kind: new_patch
    description: '为 update_curr_fair/sched.h 的 curr 访问补 rcu_dereference 或 __rcu 标注'
  - kind: testing
    description: '本地 make C=2 sparse 复现并验证修复'
generated_at: '2026-09-23T00:00:00'
source_email_count: 1
related_articles: []
tags:
  - cfs
  - sched_debug
---