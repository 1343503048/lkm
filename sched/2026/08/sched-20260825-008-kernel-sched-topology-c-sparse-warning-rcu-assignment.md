# kernel/sched/topology.c:2606:24: sparse: incorrect type in assignment (different address spaces)

## TL;DR

kernel test robot 报告 `kernel/sched/topology.c` 中一个 sparse 警告，bisect 到 commit 5a7b576b3ec1 ("sched/topology: Extract "imb_numa_nr" calculation into a separate helper")，该 commit 来自约 5 个月前。警告涉及 `__rcu` 地址空间不匹配的指针赋值。同时 `kernel/sched/debug.c:730` 也有类似的 `__rcu` 注解问题。

## 背景与问题

sparse 静态检查报告两类 `__rcu` 地址空间不匹配：
1. `kernel/sched/topology.c:2606` — 赋值时 expected/actual 地址空间不同
2. `kernel/sched/debug.c:730` — `sd->parent`（`__rcu *`）赋给非 `__rcu` 指针

这些是数据依赖注解的正确性问题，可能导致 RCU 保护缺失。

## 技术方案

需要修复 sparse 警告：
- topology.c 中的赋值需要使用 `rcu_assign_pointer()` 或添加 `__rcu` 注解
- debug.c 中的 `sd->parent` 访问需要使用 `rcu_access_pointer()` 或正确注解

## 版本演进与当前进展

kernel test robot 自动报告，bisect 指向 5a7b576b3ec1（5 个月前的 commit）。等待作者 Prateek 修复。

## Maintainer 意见与讨论焦点

暂无人工讨论，仅 robot 自动报告。

## 合入评估

- **likelihood: medium** — sparse 警告修复通常会被捡起，但该 commit 已存在 5 个月
- **blocking_issues**: 无
- **next_action**: 等待 topology.c 的作者/维护者修复

## 效果评估

暂无效果数据（静态检查修复，不影响运行时行为）。

## 我可以参与的点

- **提交修复 patch**：这是一个明确的、低风险的修复机会。可以按 robot 建议的 Fixes 标签提交 sparse 警告修复
- Fixes: 5a7b576b3ec1 ("sched/topology: Extract "imb_numa_nr" calculation into a separate helper")

## 参考链接

- lore thread: https://lore.kernel.org/oe-kbuild-all/202608251448.isPvDhz8-lkp@intel.com/
- Fixes: 5a7b576b3ec1 ("sched/topology: Extract "imb_numa_nr" calculation into a separate helper")
- tip-bot commit: 未获取到

---
id: sched-20260825-008
date: 2026-08-25
subsystem: sched
type: discussion
status: under_review
severity: low
thread_root_msgid: "<202608251448.isPvDhz8-lkp@intel.com>"
lore_url: "https://lore.kernel.org/oe-kbuild-all/202608251448.isPvDhz8-lkp@intel.com/"
authors: [kernel test robot]
maintainers_involved: []
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: "5a7b576b3ec1"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: "等待 topology 维护者修复 sparse 警告"
contribution_opportunities:
  - kind: new_patch
    description: "提交 sparse 警告修复 patch，Fixes: 5a7b576b3ec1，添加正确的 __rcu 注解"
generated_at: "2026-08-27T10:00:00"
source_email_count: 1
related_articles: []
tags: [sched_debug]
---
