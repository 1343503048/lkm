---
id: sched-20261115-004
date: '2026-11-15'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <avmi5linMgdLjgsD@gmail.com>
lore_url: https://lore.kernel.org/all/avmi5linMgdLjgsD@gmail.com/
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
current_version: null
patch_series: []
upstream_commit: ec6f6731538e0d45872eb279fdeb477bed152d6f
fixes_commit: null
merged_branch: sched-urgent-2026-11-15
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 pr-tracker-bot 合并确认
  next_action: 等待 Linus 合入，关注五修复各自的 stable 回合
contribution_opportunities:
- kind: review
  description: 核对 OLK-6.6 等旧分支回合五修复时代码路径是否同构
- kind: testing
  description: 在 v7.4/stable 上回归 uclamp 校验、cpuset 解锁与 SMT hotplug 路径
generated_at: '2026-11-16T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- deadline
- uclamp
- cgroup
- load_balance
- topology
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR

Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-11-15`，顶部 commit ec6f6731538e），含五枚此前各自补丁系列已过 review 的正确性修复：deadline 迁移禁用任务假 -EPERM、uclamp 拒绝超 SCHED_CAPACITY_SCALE 的 clamp、__sched_setscheduler 的 cpuset_mutex 二次解锁、invalid_llc_nr 不用 fits_capacity 比较线程/CPU 数、CPU onlining 不触碰未 join core 的 SMT siblings。当日缓存未见 Linus 合并回帖。

## 背景与问题

合入窗口期 Ingo 汇总 sched/urgent 分支的五枚修复发 pull。五枚修复均为此前独立补丁系列里已通过 review 的正确性修复（分别对应 sched/deadline、sched/uclamp、sched/core、sched/cache 子系统），其背景与合入过程散见于各自系列的历史文章。

## 技术方案

本轮无新代码，为 sched/urgent 五修复的合入确认 pull。具体组成：

- Andrea Parri（3 枚）：sched/deadline 修复迁移禁用任务假 -EPERM；sched/uclamp 拒绝高于 SCHED_CAPACITY_SCALE 的 clamp 值；sched/core 修复 __sched_setscheduler() 的 cpuset_mutex 二次解锁。
- Zhan Xusheng（1 枚）：sched/cache 的 invalid_llc_nr() 不再用 fits_capacity() 比较线程数与 CPU 数。
- Seiji Nishikawa（1 枚）：sched/core 在 CPU onlining 时不触碰尚未 join core 的 SMT siblings。

diffstat：5 文件 +37/-14（core.c / core_sched.c / fair.c / sched.h / syscalls.c）。

## 版本演进与当前进展

*current_version: null（GIT PULL，无版本化补丁）*。当日进展：五修复由 Ingo 发 pull，等待 Linus 收取。

## Maintainer 意见与讨论焦点

无争议。五修复均已过 review，Ingo 作为维护者汇总收取并向 Linus 发 pull。无 NAK。

## 合入评估

*likelihood=high*。五修复已进 tip/sched/urgent 并被 Ingo 发 pull；当日缓存未见 pr-tracker-bot 合并确认。*blocking_issues*：等待 Linus 收取。*next_action*：关注 Linus 合入与五修复各自的 stable 回合。

## 效果评估

无量化数据，属正确性修复集（假 -EPERM、clamp 校验、mutex 解锁、fits_capacity 逻辑、SMT 生命周期）。

## 我可以参与的点

- **review**：核对 OLK-6.6 等旧分支回合这五修复时代码路径是否同构（尤其 delayed dequeue / core_sched 相关路径是否存在上下文差异）。
- **testing**：在 v7.4 或 stable 上回归 uclamp 校验、cpuset 解锁与 SMT hotplug 路径。

## 参考链接

- lore thread: https://lore.kernel.org/all/avmi5linMgdLjgsD@gmail.com/
