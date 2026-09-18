---
id: sched-20260918-022
date: '2026-09-18'
subject: 'kernel/sched/idle.c:511:45: sparse: sparse: incorrect type in argument 1
  (different address spaces)'
subsystem: sched
type: bug
status: stalled
severity: low
thread_root_msgid: <202609180239.7Jr6Miwi-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202609180239.7Jr6Miwi-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <202609180239.7Jr6Miwi-lkp@intel.com>
  date: '2026-09-18'
  summary: sparse 报告 idle.c/rt.c 的 __rcu 地址空间标注缺失
  review_outcome: 无回应
upstream_commit: null
fixes_commit: ca3aec453d64
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无修复者认领
  next_action: 补齐 curr/donor 的 __rcu 标注并提交修复
contribution_opportunities:
- kind: new_patch
  description: 补齐 idle.c/rt.c 的 __rcu 标注（加 Fixes/Closes 标签）
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_debug
- idle
title: 'kernel/sched/idle.c:511:45: sparse: sparse: incorrect type in argument 1 (different
  address spaces)'
layout: article
---

## TL;DR
kernel test robot 的 sparse（W=1）报告：`kernel/sched/idle.c:511:45` 把 `struct task_struct __rcu *curr` 传给期望 `const struct task_struct *` 的形参，地址空间标注不匹配；同报告还列出 `kernel/sched/rt.c` 多处 donor 的 `__rcu` 标注缺失。定位到 commit ca3aec453d64（sched_ext update_idle 路由，9 周前）。当前无人认领修复。

## 背景与问题
sparse（v0.6.5-rc1，clang 22.1.3，x86_64-randconfig）在 master（head 9b87fdc9af2f）上报告：`idle.c:511:45` 期望 `struct task_struct const *p` 却得到 `[noderef] __rcu *curr`；`rt.c` 多处（2325/976/1498/1826/1517）对 `donor`/`parent` 的 `__rcu` 标注也缺失。属 proxy/执行上下文拆分后 `curr`/`donor` 的 RCU 注解未补齐一类问题。报告建议 Fixes: ca3aec453d64。

## 技术方案
无补丁——这是静态分析报告。修复方向：为相关 `curr`/`donor` 指针补齐 `__rcu` 标注或使用 `rcu_dereference` 系列访问。

## 版本演进与当前进展
- 首报（09-18，`<202609180239.7Jr6Miwi-lkp@intel.com>`）：本日无后续。

## Maintainer 意见与讨论焦点
- 无维护者回应。属 0-day robot 报告，通常由相关子系统作者认领并修 `__rcu` 标注。

## 合入评估
likelihood=low。纯 W=1 静态告警、无运行时影响，且无认领人。blocking_issues：无修复者认领；仅稀疏告警。next_action：相关 maintainer 或作者认领，补齐 `__rcu` 标注并加 Fixes/Closes 标签提交修复。

## 效果评估
无性能/运行时影响；sparse W=1 编译期地址空间告警。

## 我可以参与的点
- kind=new_patch：补齐 `idle.c`/`rt.c` 中 `curr`/`donor` 的 `__rcu` 标注（加 Fixes/Reported-by/Closes 标签），这类注解修复通常易被快速收取。

## 参考链接
- lore（报告）: https://lore.kernel.org/all/202609180239.7Jr6Miwi-lkp@intel.com/
