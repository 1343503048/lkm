---
id: sched-20260918-023
date: '2026-09-18'
subject: 'kernel/sched/topology.c:1037:21: sparse: sparse: incorrect type in assignment
  (different address spaces)'
subsystem: sched
type: bug
status: stalled
severity: low
thread_root_msgid: <202609180028.7pOuivmX-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202609180028.7pOuivmX-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <202609180028.7pOuivmX-lkp@intel.com>
  date: '2026-09-18'
  summary: sparse 报告 topology.c/debug.c 的 __rcu 标注缺失
  review_outcome: 无回应
upstream_commit: null
fixes_commit: 5beff4f08727
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 无修复者认领
  next_action: 补齐 sched_domain 指针的 __rcu 标注并提交修复
contribution_opportunities:
- kind: new_patch
  description: 补齐 debug.c/topology.c 的 __rcu 标注（加 Fixes/Closes 标签）
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles: []
tags:
- sched_debug
- topology
title: 'kernel/sched/topology.c:1037:21: sparse: sparse: incorrect type in assignment
  (different address spaces)'
layout: article
---

## TL;DR
kernel test robot 的 sparse（W=1）报告：`kernel/sched/topology.c:1037:21` 对 `struct sched_domain *sd` 赋值了 `[noderef] __rcu *parent`，地址空间标注不匹配；同报告还列出 `debug.c`（788/1129）与 `topology.c`（118/137）多处 `sd`/`tsk` 的 `__rcu` 标注缺失。定位到 commit 5beff4f08727（sched/cache 多 LLC 修复，4 个月前）。当前无人认领。

## 背景与问题
sparse（v0.6.5-rc1，clang 24.0.0git，powerpc64-randconfig）在 master（head 9b87fdc9af2f）上报告：`topology.c`/`debug.c` 多处对 `sched_domain`/`task_struct` 指针的 `__rcu` 标注缺失（`parent`/`child`/`curr` 等），属 sched domain 遍历与 debug 接口的 RCU 注解不完整。报告建议 Fixes: 5beff4f08727。

## 技术方案
无补丁——静态分析报告。修复方向：为相关 `sched_domain`/`task_struct` 指针补齐 `__rcu` 标注或使用 `rcu_dereference` 系列访问。

## 版本演进与当前进展
- 首报（09-18，`<202609180028.7pOuivmX-lkp@intel.com>`）：本日无后续。

## Maintainer 意见与讨论焦点
- 无维护者回应。属 0-day robot 报告。

## 合入评估
likelihood=low。纯 W=1 静态告警、无运行时影响且无认领人。blocking_issues：无认领者。next_action：相关 maintainer 认领并补齐 `__rcu` 标注，加 Fixes/Closes 标签提交修复。

## 效果评估
无性能/运行时影响；sparse W=1 编译期地址空间告警。

## 我可以参与的点
- kind=new_patch：补齐 `debug.c`/`topology.c` 中 sched_domain 指针的 `__rcu` 标注（加 Fixes/Reported-by/Closes 标签）。

## 参考链接
- lore（报告）: https://lore.kernel.org/all/202609180028.7pOuivmX-lkp@intel.com/
