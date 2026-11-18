---
id: sched-20261118-022
date: '2026-11-18'
subject: 'sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261107113639.GK2668200@noisy.programming.kicks-ass.net>
lore_url: https://lore.kernel.org/all/20261107113639.GK2668200@noisy.programming.kicks-ass.net/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
current_version: v2
patch_series:
- version: v2
  msgid: <20261107113639.GK2668200@noisy.programming.kicks-ass.net>
  date: '2026-11-07'
  summary: cfs_rq::idle 改为祖先 tg::idle 之和
  review_outcome: Vincent/Kayra/Josh RB，合入 sched/urgent
upstream_commit: 75545668ae0fd80c08fe8fd0c6799b2ba9284557
fixes_commit: 85570f10a4c6
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 sched/urgent 进入 7.4-rc 修复
contribution_opportunities: []
generated_at: '2026-11-19T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261112-018
tags:
- cfs
- cgroup
- eevdf
title: 'sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle'
layout: article
---

## TL;DR

Peter Zijlstra 的 cgroup SCHED_IDLE 抢占修复 **patch 2 今日合入 tip/sched/urgent**（commit `75545668ae0f`）：把 `cfs_rq::idle` 从「tg::idle 的拷贝」改为「所有祖先 tg::idle 之和」，使 `se_is_idle()` 能感知祖先路径上任意一层的 idle cgroup，修复单 runqueue 化后 flatten runqueue 时被忽略的 cgroup::idle 抢占问题（Fixes: 85570f10a4c6）。此前 0-day 抓到的 `!CONFIG_FAIR_GROUP_SCHED` 构建失败（`idle` 成员位置错误）已随合入修复。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/12/sched-20261112-018-sched-fair-make-cfs-rq-idle-the-sum-of-ancestor-tg-idle.html">sched-20261112-018</a>）cgroup SCHED_IDLE 任务组的抢占语义：`cfs_rq::idle` 此前只反映本组自身 idle 状态、未聚合祖先，导致嵌套 idle 判定错误。patch 2 用「`cfs_rq::idle` = 祖先 tg::idle 之和」修复；此前该成员放在 `CONFIG_FAIR_GROUP_SCHED` 保护之外，0-day 抓到 `!CONFIG_FAIR_GROUP_SCHED` 构建失败，Kayra 给出下移修法。

## 技术方案

（承接）`kernel/sched/fair.c`（+56/-35 量级）+ `kernel/sched/debug.c` + `kernel/sched/sched.h`：`cfs_rq::idle` 改为祖先 tg::idle 之和，`se_is_idle()` 语义随之变化。已获 Vincent/Kayra/Josh 三方 Reviewed-by。

## 版本演进与当前进展

已合入 tip/sched/urgent（`75545668ae0f`，AuthorDate 2026-11-07，CommitterDate 2026-11-18）。

## Maintainer 意见与讨论焦点

- **Peter Zijlstra（作者/维护者）**：作为 Author+Committer 合入。
- 已有 Vincent Guittot、Kayra Cizmeci、Josh Don 的 Reviewed-by（见 commit message）。
- 无 NAK；已合入。

## 合入评估

*likelihood=merged*。已合入 tip/sched/urgent（`75545668ae0f`）。*blocking_issues*：无。*next_action*：随 sched/urgent 进入 7.4-rc 修复。

## 效果评估

无量化性能数据，属抢占语义正确性修复；此前 Vincent 确认可避免 `find_matching_se()` 无谓调用。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入）。

## 参考链接

- tip 合入: https://git.kernel.org/tip/75545668ae0fd80c08fe8fd0c6799b2ba9284557
- lore thread: https://lore.kernel.org/all/20261107113639.GK2668200@noisy.programming.kicks-ass.net/
