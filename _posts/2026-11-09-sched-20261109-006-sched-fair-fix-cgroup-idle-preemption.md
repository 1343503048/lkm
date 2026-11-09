---
id: sched-20261109-006
date: '2026-11-09'
subject: 'sched/fair: Fix cgroup::idle preemption'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <CAKfTPtADXBuv4TfnVt+woL8Qz-8aX=wgnKTg6oiK=Tegw7cdyA@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CAKfTPtADXBuv4TfnVt+woL8Qz-8aX=wgnKTg6oiK=Tegw7cdyA@mail.gmail.com/
authors:
- Peter Zijlstra
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v2
patch_series:
- version: v2
  msgid: <20261107113639.GK2668200@noisy.programming.kicks-ass.net>
  date: '2026-11-07'
  summary: patch 2 v2 把 cfs_rq::idle 改为祖先 tg::idle 之和，并入竞态修正
  review_outcome: Kayra 双 Reviewed-by，Vincent 今日补 Reviewed-by
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - patch 2 是否补 Fixes 标签待定
  next_action: Peter 收取 patch 1/2，patch 3 继续推进
contribution_opportunities:
- kind: review
  description: 审查 patch 3 RFC 的 find_matching_se() 改法（Peter 曾质疑、仍处 RFC）
generated_at: '2026-11-10T09:00:00+08:00'
source_email_count: 1
related_articles:
- sched-20261106-003
- sched-20261107-005
tags:
- cgroup
- cfs
- eevdf
title: 'sched/fair: Fix cgroup::idle preemption'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-003-sched-fair-fix-cgroup-idle-preemption.html">sched-20261106-003</a>：Peter Zijlstra 发出 3 补丁系列修复 cgroup SCHED_IDLE 任务组的抢占问题：patch 1 用 guard 清理 `sched_group_set_idle()`、patch 2 把 `cfs_rq::idle` 改为「祖先 tg::idle 之和」、patch 3（RFC）携带 Vincent 的 `sched/eevdf: Fix sched idle task group preemption`。Kayra 指出 patch 2 有任务组创建竞态并追问 `se_is_idle()`；Peter 补上判定。
- <a class="article-ref" href="/lkm/2026/11/07/sched-20261107-005-sched-fair-fix-cgroup-idle-preemption.html">sched-20261107-005</a>：Peter 发出 patch 2 v2（并入竞态修正）；Kayra 给 patch 2 v2 与 patch 3 RFC 双 Reviewed-by；Vincent 给 patch 1 Reviewed-by。
- <a class="article-ref" href="/lkm/2026/11/09/sched-20261109-006-sched-fair-fix-cgroup-idle-preemption.html">sched-20261109-006</a>（今天）：**Vincent Guittot 给 patch 2 v2（`sched/fair: Make cfs_rq::idle the sum of ancestor tg::idle`）补上 Reviewed-by**，至此 patch 1/2 均已获 Vincent + Kayra 双维护者评审，patch 3 仍为 RFC。

## 背景与问题

（承接 <a class="article-ref" href="/lkm/2026/11/06/sched-20261106-003-sched-fair-fix-cgroup-idle-preemption.html">sched-20261106-003</a> / 20261107-005）cgroup SCHED_IDLE 任务组的抢占语义问题：`cfs_rq::idle` 此前只反映本组自身的 idle 状态，未聚合祖先任务组的 idle 状态，导致 idle 任务组在某些嵌套场景下抢占判定错误。Peter 的系列用「`cfs_rq::idle` = 祖先 tg::idle 之和」来修复，并为 patch 3 的 EEVDF 抢占优化打底。

## 技术方案

patch 2（`Make cfs_rq::idle the sum of ancestor tg::idle`）把 `cfs_rq::idle` 从「本组 idle 标志」改为「祖先 tg::idle 之和」，使嵌套 idle 判定正确；v2 并入 Kayra 指出的任务组创建竞态修正（需 rq->lock）。今日 Vincent 确认该补丁「对 `wakeup_preempt_sched_idle()` 第一处检查是必要的，可避免对 `find_matching_se()` 的无谓调用」，并给 Reviewed-by。

## 版本演进与当前进展

*current_version: v2（patch 2，2026-11-07 发出）*。今日：Vincent 对 patch 2 v2 补 Reviewed-by。至此三补丁中 patch 1/2 已获 Kayra + Vincent 双评审（Kayra 建议 patch 2 补 Fixes 标签），patch 3（RFC）仍在演进。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：今日对 patch 2 v2 给 Reviewed-by；此前已对 patch 1 给 Reviewed-by。
- **Kayra Cizmeci**：此前对 patch 2 v2 与 patch 3 RFC 双 Reviewed-by（「我最初的老顾虑已解决」），建议 patch 2 补 Fixes。
- 无 NAK。系列明显收敛：patch 1/2 基本可收，patch 3 仍带 RFC 标记、`find_matching_se()` 曾遭 Peter 本人质疑。

## 合入评估

*likelihood=high*（对 patch 1/2）。patch 1/2 已获双维护者评审，可独立收取；patch 3 仍 RFC 需继续演进。*blocking_issues*：① patch 2 是否补 Fixes 待作者/Peter 定；② patch 3 尚未定型。*next_action*：Peter 收取 patch 1/2（或先补 Fixes 后收），patch 3 继续推进。

## 效果评估

无量化性能数据，属抢占语义正确性修复。Vincent 确认 patch 2 可避免 `find_matching_se()` 的无谓调用（微观优化，未见 benchmark）。

## 我可以参与的点

- **review**：审查 patch 3 RFC（`sched/eevdf: Fix sched idle task group preemption` 的 `find_matching_se()` 改法）——这是 Peter 本人质疑过、仍处 RFC 的点，值得深入。

## 参考链接

- Vincent 对 patch 2 v2 的 Reviewed-by: https://lore.kernel.org/all/CAKfTPtADXBuv4TfnVt+woL8Qz-8aX=wgnKTg6oiK=Tegw7cdyA@mail.gmail.com/
