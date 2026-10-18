---
id: sched-20261018-012
date: 2026-10-18
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <atSQkrxwvS17naGH@gmail.com>
lore_url: https://lore.kernel.org/all/atSQkrxwvS17naGH@gmail.com/
authors:
- Ingo Molnar
maintainers_involved:
- Ingo Molnar
current_version: null
patch_series: []
upstream_commit: 2f93bcb3f9aaf6ceee1aec0a97d4fe386d48e781
fixes_commit: null
merged_branch: sched-urgent-2026-10-18
merge_assessment:
  likelihood: high
  blocking_issues:
  - 当日缓存未见 pr-tracker-bot 合并确认
  next_action: 等待 Linus 合入，关注两修复的 stable 回合
contribution_opportunities:
- kind: testing
  description: 回归 sched_setscheduler 类变更（RCU 压力）与 EEVDF vlag 缩放边界
generated_at: '2026-10-19T09:00:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- eevdf
title: '[GIT PULL] scheduler fixes'
layout: article
---

## TL;DR

Ingo Molnar 向 Linus 发 sched/urgent 修复 pull request（tip 树 `sched-urgent-2026-10-18`，截至 `2f93bcb3f9aaf6ceee1aec0a97d4fe386d48e781`），含两枚修复：`__sched_setscheduler()` 类变更竞态导致丢 resched（K Prateek Nayak，近期 RCU 改动暴露）、`place_entity()` vlag 缩放的 s64 乘法溢出可破坏实体位置（Hui Su）。kernel test robot 已确认 tip/sched/urgent `BUILD SUCCESS`。当日缓存未见 Linus 合并回帖。

## 背景与问题

合入窗口期 Ingo 另发一条 `sched/urgent` 修复 pull，收集两枚此前已 review 的修复：

- **类变更竞态丢 resched**：`__sched_setscheduler()` 改变任务类时的竞态可能导致丢失 reschedule，被近期的 RCU 改动暴露（K Prateek Nayak）。
- **vlag 缩放乘法溢出**：`place_entity()` 里 vlag 缩放的 s64 乘法溢出，可破坏实体的（在 EEVDF 树中的）位置（Hui Su）。

## 技术方案

两枚 commit（`kernel/sched/core.c` +19/−12、`kernel/sched/fair.c` +16/−4，合计 +21/−14）：

- K Prateek Nayak：`sched/core: Call wakeup_preempt() for queued tasks during class change`
- Hui Su：`sched/fair: Avoid overflow in place_entity()`

## 版本演进与当前进展

*current_version: null*。pull request 当日发出（2026-10-18，`<atSQkrxwvS17naGH@gmail.com>`）；kernel test robot 同日确认 tip/sched/urgent `BUILD SUCCESS 2f93bcb3f9aaf6ceee1aec0a97d4fe386d48e781`。缓存内未见 Linus 合并回帖。

## Maintainer 意见与讨论焦点

Ingo Molnar（调度 maintainer）作为发起人汇总；两枚修复均在此前各自补丁系列中已通过 review（place_entity 见 <a class="article-ref" href="/lkm/2026/10/15/sched-20261015-006-sched-fair-avoid-overflow-in-place-entity.html">sched-20261015-006</a>/016-007，wakeup_preempt 见 <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-001-sched-core-call-wakeup-preempt-for-queued-tasks-during-class.html">sched-20261013-001</a>/014-001）。无争议。

## 合入评估

*likelihood=high*。两枚修复均已过 review 并进 tip/sched/urgent，kernel test robot 确认构建成功；窗口期的 urgent 修复 pull 通常很快被 Linus 收取。*blocking_issues*：当日缓存未见 pr-tracker-bot 合并确认。*next_action*：等待 Linus 合入；两枚修复的 stable 回合与否视各自补丁的 Cc 而定。

## 效果评估

无量化数据，属正确性修复集：一个修类变更丢 resched 的竞态、一个修 vlag 缩放乘法溢出。二者都是隐蔽的正确性问题，效果以「消除竞态/溢出」为准。

## 我可以参与的点

- `testing`：在 v7.4 窗口或 7.3 stable 上回归 `sched_setscheduler` 类变更（配合 RCU 压力）与 EEVDF vlag 缩放边界（极端 nice/权重），确认两修复无新回归。
- 回合视角：OLK-6.6 回合 `place_entity()` 溢出修复时应先确认 6.6 的 vlag 缩放代码路径是否同构（上游含 EEVDF 重构，需对照）。

## 参考链接

- GIT PULL：https://lore.kernel.org/all/atSQkrxwvS17naGH@gmail.com/
- tip/sched/urgent BUILD SUCCESS：https://lore.kernel.org/all/202610180313.nI1jjRFN-lkp@intel.com/
