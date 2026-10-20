---
id: sched-20261020-007
date: 2026-10-20
subject: 'sched_ext: Reset runnable_at when a task leaves its scheduler'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20261019124146.3582127-1-michalblk@google.com>
lore_url: https://lore.kernel.org/all/20261019124146.3582127-1-michalblk@google.com/
authors:
- Michal Blaszczyk
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v1
patch_series:
- version: v1
  msgid: <20261019124146.3582127-1-michalblk@google.com>
  date: 2026-10-19
  summary: 两补丁：任务离开 SCX 时重置 runnable_at 避免 watchdog 误报 stall + class_switch_stall
    selftest
  review_outcome: 'Andrea 复现并给 1/2 Reviewed-by；Tejun 今日应用 for-7.4-fixes 并补 Cc: stable
    v6.12+'
upstream_commit: null
fixes_commit: null
merged_branch: sched_ext/for-7.4-fixes
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 随 for-7.4 合入主线，观看 stable 回补（v6.12+）
contribution_opportunities:
- kind: testing
  description: 在 ≥6.12 stable 上验证 class_switch_stall selftest 无脆弱超时
- kind: review
  description: 核对 runnable_at 重置时机是否覆盖任务离开 SCX 的全部路径
generated_at: '2026-10-21T01:30:00'
source_email_count: 1
related_articles:
- sched-20261019-012
tags:
- sched_ext
title: 'sched_ext: Reset runnable_at when a task leaves its scheduler'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/19/sched-20261019-012-sched-ext-reset-runnable-at-when-a-task-leaves-its-scheduler.html">sched-20261019-012</a>：Michal Blaszczyk（Google）发往 sched_ext 的两补丁——任务在等待中离开 SCHED_EXT 时 `runnable_at` 未重置，watchdog 会把 SCHED_EXT 外的时间计入「等待时长」、误报 stall 并中止调度器；1/2 修复、2/2 加 `class_switch_stall` selftest；Andrea Righi 复现并给 1/2 `Reviewed-by`，2/2 只有一条 selftest 超时余量的稳健性建议。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-007-sched-ext-reset-runnable-at-when-a-task-leaves-its-scheduler.html">sched-20261020-007</a>（今天）：Tejun Heo 应用该系列到 `sched_ext/for-7.4-fixes`，并附加标签 `Cc: stable@vger.kernel.org # v6.12+` 与 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`。

## 背景与问题

（承接 20261019-012）sched_ext 的 watchdog 用 `runnable_at` 判断任务「等待过长」。若任务在等待时被切出 SCHED_EXT（BPF 调度器在唤醒后仍把它留在 DSQ 上等待），测试场景把它切到 SCHED_OTHER、睡过三倍 watchdog 超时再切回并唤醒，watchdog 若把 SCHED_EXT 之外的时间也计入，会误报 stall 并 abort 调度器。修复方案是任务离开 sched_ext 时重置 `runnable_at`，使 watchdog 只对 SCHED_EXT 内的等待时间计时。

## 技术方案

（承接，今日为合入）两补丁：1/2 在任务离开 sched_ext 时重置 `runnable_at`；2/2 新增 `class_switch_stall` selftest 验证该场景不再误报。Tejun 今日应用到 `sched_ext/for-7.4-fixes`，并追加 `Cc: stable # v6.12+` 与 `Reviewed-by: Andrea Righi`。

## 版本演进与当前进展

*current_version: v1*。当日系列（20261019-012）→ 今日 Tejun 应用并补 stable/Reviewed-by 标签。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）今日收取：「Applied to sched_ext/for-7.4-fixes」，并追加 `Cc: stable@vger.kernel.org # v6.12+`、`Reviewed-by: Andrea Righi`。此前 Andrea 对 2/2 的 selftest 超时余量稳健性建议（watchdog timeout=3s、park=2s）是否已折入，今日回帖未明说。

## 合入评估

*likelihood=merged*。已应用到 `sched_ext/for-7.4-fixes`，带 stable 标签（v6.12+），将随 for-7.4 合入主线并回补 stable。*blocking_issues*：无（已合入维护者树）。*next_action*：随 for-7.4 进入主线，并观看 stable 回补（v6.12+）。

## 效果评估

无性能数据，属正确性修复。Andrea 此前复现了误报（「reproduced the issue」），2/2 selftest 用于证明修复有效。

## 我可以参与的点

- `testing`：在较老的 stable（≥6.12 with sched_ext）上验证回补后 `class_switch_stall` 及相关 selftest 无脆弱超时。
- `review`：核对 `runnable_at` 重置时机是否覆盖「任务在等待/运行中离开 SCX」的全部路径（此前已有此建议，进一步独立验证）。

## 参考链接

- Tejun 今日回帖（Applied）：https://lore.kernel.org/all/6e866687d1c01a62e1f277b4f2bbcb41@kernel.org/
- 封面信：https://lore.kernel.org/all/20261019124146.3582127-1-michalblk@google.com/
