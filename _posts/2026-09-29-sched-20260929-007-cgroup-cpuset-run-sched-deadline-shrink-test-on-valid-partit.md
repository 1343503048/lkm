---
id: sched-20260929-007
date: '2026-09-29'
subject: 'cgroup/cpuset: Run SCHED_DEADLINE shrink test on valid partition root only'
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: <20260927215319.382422-1-longman@redhat.com>
lore_url: https://lore.kernel.org/all/20260927215319.382422-1-longman@redhat.com/
authors:
- Waiman Long
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20260927163454.345463-1-longman@redhat.com>
  date: '2026-09-28'
  summary: 把 v1 检查拆回 cpuset1_validate_change()，引入 is_in_v2_mode()/cpuset_v2()
  review_outcome: 评审建议 v1 代码原样保留
- version: v2
  msgid: <20260927215319.382422-1-longman@redhat.com>
  date: '2026-09-28'
  summary: v1 用 is_cpu_exclusive()、v2 用 is_partition_valid() 切换判据
  review_outcome: Guopeng Zhang Reviewed-by；09-29 Tejun Applied 1-2 to cgroup/for-7.4
upstream_commit: null
fixes_commit: a86ce68078b2
merged_branch: cgroup/for-7.4
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪 7.4 合并窗口 cgroup PR 带上本修复
contribution_opportunities:
- kind: testing
  description: 在 for-7.4 内核上跑 SCHED_DEADLINE + 收缩非有效 partition root 场景确认无 -EBUSY
generated_at: '2026-09-30T01:15:00'
source_email_count: 1
related_articles:
- sched-20260928-003
tags:
- cgroup
- deadline
title: 'cgroup/cpuset: Run SCHED_DEADLINE shrink test on valid partition root only'
layout: article
---

> **subject**：`cgroup/cpuset: Run SCHED_DEADLINE shrink test on valid partition root only`

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-003-cgroup-cpuset-run-sched-deadline-shrink-test-on-valid-partit.html">sched-20260928-003</a>：Waiman Long 修复 cpuset 里 SCHED_DEADLINE 带宽收缩检查的误触发——非有效 partition root 的 cpuset 仍被置 CS_CPU_EXCLUSIVE，`validate_change()` 的 shrink 测试在有 deadline 任务的系统里被误触发，导致改 cpuset 控制文件意外 `-EBUSY`。v2 用「v1 走 `is_cpu_exclusive()`、v2 走 `is_partition_valid()`」切换判据，已获 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/09/29/sched-20260929-007-cgroup-cpuset-run-sched-deadline-shrink-test-on-valid-partit.html">sched-20260929-007</a>（今天）：Tejun Heo 回复「Applied 1-2 to cgroup/for-7.4」，本系列两片补丁正式合入 cgroup 树，将随 7.4 合并窗口进 mainline。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-003-cgroup-cpuset-run-sched-deadline-shrink-test-on-valid-partit.html">sched-20260928-003</a>）commit f82f80426f7a 在 `validate_change()` 加了「收缩带 CS_CPU_EXCLUSIVE 的 v1 exclusive cpuset 时要保证足够带宽容纳 SCHED_DEADLINE 任务」的检查；引入 cgroup v2 partition 后继续给 partition root 设 CS_CPU_EXCLUSIVE，但存在「并非有效 partition root 的 cpuset 却被错误置 exclusive 标志」的情况，导致有 deadline 任务时该检查误触发、回 `-EBUSY`。今天背景无新增，进展是合入。

## 技术方案

（承接 <a class="article-ref" href="/lkm/2026/09/28/sched-20260928-003-cgroup-cpuset-run-sched-deadline-shrink-test-on-valid-partit.html">sched-20260928-003</a>）让 shrink 测试只在有效 partition root 上触发，核心条件从 `is_cpu_exclusive(cur) && is_sched_load_balance(cur)` 改为 `(is_partition_valid(cur) || (!cpuset_v2() && is_cpu_exclusive(cur))) && is_sched_load_balance(cur)`；v2 版本不改动 v1 代码、仅切换 v1/v2 的判据函数。

## 版本演进与当前进展

*current_version: v2*（`<20260927215319.382422-1-longman@redhat.com>`）。v2 已获 Guopeng Zhang `Reviewed-by`；09-29 Tejun Heo 收「Applied 1-2 to cgroup/for-7.4」。

## Maintainer 意见与讨论焦点

- **Tejun Heo**（cgroup 维护者，09-29）：`Applied 1-2 to cgroup/for-7.4.`，正式收取。
- **Guopeng Zhang**（09-28）：`Reviewed-by`。
- 无 NAK，无遗留争议。

## 合入评估

*likelihood=merged*。两片补丁已合入 cgroup/for-7.4（`Fixes:` 明确、有 peer Reviewed-by、维护者收取）。*blocking_issues*：无（等待 7.4 合并窗口随 cgroup PR 进 mainline）。*next_action*：跟踪 7.4 合并窗口 cgroup PR 是否带上本修复（以及后续是否需要回合 stable）。

## 效果评估

无性能数据；属功能正确性修复——修复后「SCHED_DEADLINE 任务 + 收缩非有效 partition root cpuset」不再误触发 `-EBUSY`。

## 我可以参与的点

- `testing`：在 v2 已合入 for-7.4 的内核上跑「SCHED_DEADLINE + 收缩非有效 partition root」场景，确认无 `-EBUSY` 且无回归。

## 参考链接

- lore（v2 cover）: https://lore.kernel.org/all/20260927215319.382422-1-longman@redhat.com/
- Tejun 收取: https://lore.kernel.org/all/dd3f091c8b820c4c0ab39aa737d662da@kernel.org/
