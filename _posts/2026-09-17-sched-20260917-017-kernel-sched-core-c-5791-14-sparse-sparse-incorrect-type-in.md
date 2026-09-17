---
id: sched-20260917-017
date: '2026-09-17'
subject: 'kernel/sched/core.c:5791:14: sparse: sparse: incorrect type in assignment
  (different address spaces)'
subsystem: sched
type: bug
status: under_review
severity: low
thread_root_msgid: <202609172041.ahqSILHp-lkp@intel.com>
lore_url: https://lore.kernel.org/all/202609172041.ahqSILHp-lkp@intel.com/
authors:
- kernel test robot
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: f5741d2b3451
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无回帖、无补丁
  next_action: 等待 sched 维护者决定修复或忽略
contribution_opportunities:
- kind: new_patch
  description: 定位 core.c:5791 地址空间混用，提交带 Fixes/Reported-by 的小补丁
generated_at: '2026-09-18T09:00:00'
source_email_count: 1
related_articles: []
tags:
- proxy_execution
title: 'kernel/sched/core.c:5791:14: sparse: sparse: incorrect type in assignment
  (different address spaces)'
layout: article
---

## TL;DR
0day 机器人报告内核主线（commit f5741d2b3451 "sched/core: Call wq_worker_tick() for the execution context"，7 天前）在 x86_64-randconfig + W=1 下 kernel/sched/core.c 出现新的 sparse 地址空间类型告警。无回帖、无补丁，属低危构建期类型安全噪音。

## 背景与问题
sparse 静态检查在 `kernel/sched/core.c:5791` 报告 `incorrect type in assignment (different address spaces)`——通常涉及 `__rcu` / `__percpu` 等地址空间注解与裸指针混用。该告警被标记为"新（>>）"，由 7 天前的提交 f5741d2b3451（wq_worker_tick 执行上下文改动，proxy execution 相关）引入。同批还列出几处既有告警（core.c:337、843，为 `__rcu *` 与裸指针比较）。

## 技术方案
机器人建议：若用单独补丁修复，加 `Fixes: f5741d2b3451`、`Reported-by: kernel test robot`、`Closes:` 指向 oe-kbuild-all 归档。尚未有修复补丁。

## 版本演进与当前进展
仅有 bug 报告，无后续补丁或回帖。

## Maintainer 意见与讨论焦点
当日无维护者表态；相关提交对象（proxy execution / sched core）的维护者未回应。

## 合入评估
likelihood=unknown。仅 W=1 + randconfig 下的编译期告警，常规构建不受影响，缺处理压力；且无人回帖，无法判断是否会单独修、并入下一批 fix、或视作噪音不处理。blocking_issues：无回帖无补丁。next_action：等待 sched 维护者决定是否修复或忽略。

## 效果评估
无运行时影响；属构建期类型安全告警。

## 我可以参与的点
- kind=new_patch：定位 core.c:5791 的地址空间混用（`__rcu`/`__percpu` 注解缺失或取舍不当），提交带 Fixes/Reported-by 的小补丁。

## 参考链接
- lore（0day 报告）: https://lore.kernel.org/all/202609172041.ahqSILHp-lkp@intel.com/
