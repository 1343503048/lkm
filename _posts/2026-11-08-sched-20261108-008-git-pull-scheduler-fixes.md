---
id: sched-20261108-008
date: '2026-11-08'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: <avA9aDPBDzVlUqcF@gmail.com>
lore_url: https://lore.kernel.org/all/avA9aDPBDzVlUqcF@gmail.com/
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
current_version: null
patch_series: []
upstream_commit: 006991aa89974378ee579416dba87adc22cd60fd
fixes_commit: null
merged_branch: sched-urgent-2026-11-08
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 pr-tracker-bot 合并确认
  next_action: 等待 Linus 合入，关注六修复的 stable 回合
contribution_opportunities:
- kind: testing
  description: 回归 PELT 周期计数、cluster 感知调度与 delayed dequeue 的 I/O 等待记账
- kind: review
  description: 核对 OLK-6.6 等旧分支回合六修复时对应代码路径是否同构
generated_at: '2026-11-09T09:00:00+08:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- deadline
- topology
- load_balance
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR

Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-11-08`，截至 `006991aa89974378ee579416dba87adc22cd60fd`），含六枚此前已过 review 的修复：dying SCHED_DEADLINE 任务切 class 的 this_bw 缺账（Nickolai Zeldovich）、I/O 等待独立于 delayed dequeue 记账（Christian Loehle）、离开 fair class 时清 throttle 状态（Daehyeon Ko）、PELT 周期计数 u32 截断（Hui Su）、cluster static-key 更新不平衡导致 cluster 感知调度被误关（Hui Su）、`alb_break_llc()` 忽略非 fair 的 current（Kayra Cizmeci）。当日缓存未见 Linus 合并回帖。

## 背景与问题

合入窗口期 Ingo 发 sched/urgent 修复 pull，收集六枚此前已在各自补丁系列中过 review 的修复（均在 11-06 日报有对应文章）：`this_bw` 在 dying 任务切 class 时未被正确归还；I/O 等待时间此前与 delayed dequeue 耦合导致记账偏差；任务离开 fair class 时 throttle 状态残留；PELT 周期计数用 u32 存储被截断；cluster 感知的 static-key 增减不平衡会误关 cluster-aware scheduling；active load balancing 的 `alb_break_llc()` 未忽略非 fair 的 current。

## 技术方案

六枚 commit（`kernel/sched/{core,deadline,fair,pelt,topology,sched.h}.c` 共 7 files +48/−25）：

- Nickolai Zeldovich：`sched/deadline: Fix this_bw on class change of a dying task`
- Christian Loehle：`sched/core: Account I/O waits independently of delayed dequeue`
- Daehyeon Ko：`sched/fair: Clear throttle state when leaving the fair class`
- Hui Su：`sched/pelt: Fix u32 truncation of the PELT period count`
- Hui Su：`sched/topology: Balance cluster static-key updates`
- Kayra Cizmeci：`sched/cache: Ignore non-fair current in alb_break_llc()`

## 版本演进与当前进展

*current_version: null*。pull 当日发出（2026-11-08，`<avA9aDPBDzVlUqcF@gmail.com>`）。缓存内未见 Linus 合并回帖。

## Maintainer 意见与讨论焦点

Ingo Molnar（调度 maintainer）作为发起人汇总；六枚修复均已过 review 并进 tip/sched/urgent（对应 11-06 的 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-021-sched-cache-ignore-non-fair-current-in-alb-break-llc.html">sched-20261106-021</a> 至 026）。无争议。

## 合入评估

*likelihood=high*。六枚修复均已过 review 并进 tip/sched/urgent，窗口期 urgent 修复 pull 通常很快被 Linus 收取。*blocking_issues*：当日缓存未见 pr-tracker-bot 合并确认。*next_action*：等待 Linus 合入；各修复的 stable 回合与否视各自补丁的 Cc 而定。

## 效果评估

无量化数据，属正确性修复集：PELT 截断修复记账精度、this_bw/throttle/IO-wait 修复记账与状态机一致性、cluster static-key 修复 cluster 感知调度不被误关、alb_break_llc 修复 active balance 逻辑。

## 我可以参与的点

- **testing**：在 v7.4 窗口或 stable 上回归 PELT 周期计数与 cluster 感知调度、delayed dequeue 的 I/O 等待记账。
- **review**：核对 OLK-6.6 等旧分支回合这六枚修复时对应代码路径是否同构（尤其 delayed dequeue 与 alb_break_llc 相关）。

## 参考链接

- GIT PULL: https://lore.kernel.org/all/avA9aDPBDzVlUqcF@gmail.com/
