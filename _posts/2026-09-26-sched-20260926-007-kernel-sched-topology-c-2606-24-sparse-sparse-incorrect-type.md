---
id: sched-20260926-007
date: 2026-09-26
subject: 'kernel/sched/topology.c:2606:24: sparse: sparse: incorrect type in assignment
  (different address spaces)'
subsystem: sched
type: bug
status: stalled
severity: low
thread_root_msgid: <202609260235.4e405lCE-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202609260235.4e405lCE-lkp@intel.com/
upstream_commit: null
fixes_commit: 5a7b576b3ec1acc2694c5b58f80cd1d44a11b2c1
merged_branch: null
current_version: null
generated_at: '2026-09-27T01:20:00'
authors:
- kernel test robot
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无修复者认领
  - 需定位 debug.c/stats.c 访问点上的 __rcu 缺失
  next_action: 相关 owner 补 rcu_dereference/__rcu 标注并提交修复
contribution_opportunities:
- kind: new_patch
  description: 为 debug.c:730/1069 与 stats.c:136 处补 rcu_dereference 或 __rcu 标注，提交小修复
source_email_count: 1
related_articles: []
tags:
- topology
- sched_debug
title: 'kernel/sched/topology.c:2606:24: sparse: sparse: incorrect type in assignment
  (different address spaces)'
layout: article
---

## TL;DR

kernel test robot 的 sparse（v0.6.5-rc1，parisc-randconfig W=1 构建）报告：把 `__rcu` 标注的 `struct sched_domain *parent` / `struct task_struct *curr` 赋给普通指针，触发 `incorrect type in assignment / argument`（different address spaces）。该告警被 bisect 到已合入 commit `5a7b576b3ec1`（"sched/topology: Extract "imb_numa_nr" calculation into a separate helper"，约 6 个月前），发信给该 commit 作者 K Prateek Nayak。属低严重度的 `__rcu` 类型标注缺失，暂无修复。

## 背景与问题

sparse 在 W=1 构建 tarball 上对 `kernel/sched/build_utility.c`（含 debug.c、stats.c）报 address-space 告警，具体三处：`kernel/sched/debug.c:730:17` 期望 `struct sched_domain *sd` 却得到 `__rcu *parent`；`debug.c:1069:9` 期望 `struct task_struct *tsk` 却得到 `__rcu *curr`（同位置重复一行）；`kernel/sched/stats.c:136:17` 同样的 sd 赋值。根因是把 rq/domain 上 `__rcu` 标注的指针直接用（未经 `rcu_dereference` 析出 `__rcu` 属性）。报告建议修复时加 `Fixes: 5a7b576b3ec1` 与 `Reported-by: kernel test robot <lkp@intel.com>`。

## 技术方案

本日仅为静态分析报告，无修复补丁。修复方向通常是给对应访问点补 `rcu_dereference()`，或在宏/赋值点析出 `__rcu` 属性。

## 版本演进与当前进展

sparse 报告（`<202609260235.4e405lCE-lkp@intel.com>`）当日发出，无开发者回复、无修复补丁。

## Maintainer 意见与讨论焦点

当日无维护者表态。此类 sparse `__rcu` 噪音通常由对应代码 owner 认领后补齐标注或加 `rcu_dereference`。报告直接发给了被 bisect 的 commit 作者 K Prateek Nayak。

## 合入评估

*likelihood=low*。无修复者认领，非运行时 bug（仅 sparse 静态类型检查），优先级低。*blocking_issues*：无修复者；需定位访问点上的 `__rcu` 缺失。*next_action*：sched/debug.c 与 stats.c 相关 owner 补 `rcu_dereference`/`__rcu` 标注并提交修复。

## 效果评估

无运行时影响；仅为 W=1 sparse 静态检查的 address-space 类型告警。

## 我可以参与的点

- `new_patch`：为 `debug.c:730/1069` 与 `stats.c:136` 处补齐 `rcu_dereference`（或调整 `__rcu` 标注）并提交修复，属直接可做的小改动。

## 参考链接

- sparse 报告: https://lore.kernel.org/all/202609260235.4e405lCE-lkp@intel.com/
- 机器人归档: https://lore.kernel.org/oe-kbuild-all/202609260235.4e405lCE-lkp@intel.com/
