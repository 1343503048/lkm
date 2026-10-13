---
id: sched-20261013-015
subject: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
date: 2026-10-13
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>
lore_url: https://lore.kernel.org/all/20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved:
- Peter Zijlstra
current_version: v6
patch_series:
- version: v5
  msgid: <20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>
  date: 2026-10-08
  summary: 非 SMT narrow reciprocal WF_SYNC 保住 waker CPU
  review_outcome: Peter 吐槽可读性/record_wakee 无守卫
- version: v6
  msgid: <20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org>
  date: 2026-10-13
  summary: in_task 守卫 + 命名布尔 reciprocal_wakeup + 非 SMT 显式化，刷新数据
  review_outcome: 当日无回帖，待 Peter 复审
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - Peter 尚未复审 v6，此前态度强烈负面
  next_action: Peter 复审 v6
contribution_opportunities:
- kind: review
  description: 复核 v6 的 in_task/reciprocal 语义是否消除 last_wakee 不稳定问题
- kind: testing
  description: 在非 SMT/SMT/异步容量平台复测 perf bench sched pipe 并验证无回归
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 2
related_articles:
- sched-20261009-005
- sched-20261012-021
tags:
- cfs
title: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
layout: article
---

> **subject**：sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-005-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261009-005</a>：Shubhang Kaushik（Ampere）发 v5——narrow reciprocal 的 `WF_SYNC` 唤醒在非 SMT 系统上保住在 wake-affine 选中的 waker CPU，不被 `select_idle_sibling()` 搬走。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-021-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261012-021</a>：Peter Zijlstra 强烈吐槽——代码难懂、!SMT 动机不清晰、`record_wakee()` 缺 `in_task()` 守卫，要求「用可读代码说服我」。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-015-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261013-015</a>（今天）：Shubhang 发 **v6** 逐条回应——`record_wakee()` 加 `in_task()` 守卫、`p->last_wakee == current` 在 `record_wakee()` 之前捕获为局部布尔 `reciprocal_wakeup`、非 SMT 限制在判断点显式化；并刷新 80 核非 SMT Ampere Altra 的 `perf bench sched pipe` 数据（mean 3.704→2.267 usec/op，约 38.8% 提升）。

## 背景与问题
（承接 20261009-005 / 20261012-021）`WF_SYNC` 唤醒下 `wake_affine()` 可能选中/保持 waker CPU，但后续 `select_idle_sibling()` 的空闲搜索可能把 wakee 搬走。pipe 式 ping-pong（A 唤醒 B、B 唤醒 A 循环）负载下，保住 wake-affine 的 waker CPU 比另找空闲 CPU 更有利。此前 v5 的实现被 Peter 批评：函数大谈 sync-pair 却未真正确保「成对」、逻辑隐晦；`last_wakee` 依赖的 `record_wakee()` 缺 `in_task()` 守卫，IRQ/softirq 里会把被中断任务误记为 waker。

## 技术方案
（承接 20261009-005）v6（`kernel/sched/fair.c` +40）：
- `record_wakee()` 开头加 `if (!in_task()) return;`——IRQ/softirq context 下 current 是被中断任务而非逻辑 waker，不再记录。
- 在 `select_task_rq_fair()` 里、调用 `record_wakee(p)` **之前**，把 `reciprocal_wakeup = in_task() && p->last_wakee == current;` 捕获为局部布尔，避免 `record_wakee()` 先行把 `current->last_wakee` 改成 p。
- 新增 `can_stack_on_waker()`：`(rq->nr_running - cfs_h_nr_delayed(rq)) == 1` 且（asym cap 活跃时）`task_fits_cpu(p, cpu)`。
- 判断点：`sync && !sched_smt_active() && new_cpu == cpu && reciprocal_wakeup && can_stack_on_waker(p, cpu)` 时直接 `return cpu`——非 SMT 上把 reciprocal WF_SYNC wakee 叠在 waker 后，SMT 系统仍走 `select_idle_sibling()`。

## 版本演进与当前进展
v6 今日首发（`<20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org>`）。相对 v5：逐条落实 Peter 三点意见（in_task 守卫、命名布尔、非 SMT 显式化），并刷新基准数据。当日无新回帖。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**（前日）：批评可读性与 `record_wakee()` 无守卫，要求可读代码说服（v6 已逐项回应，尚待其复审）。
- 无 NAK；焦点在可读性与实现正确性。

## 合入评估
*likelihood=low*。v6 已回应 Peter 的全部批评并刷新数据，但 Peter 尚未复审 v6，此前态度强烈负面。*blocking_issues*：待 Peter 复审 v6 是否认可可读性/正确性。*next_action*：Peter 复审 v6；若仍有可读性/正确性异议，作者继续迭代。

## 效果评估
v6 附 80 核非 SMT Ampere Altra、`perf bench sched pipe -l 1000000`（30 次）：
- default：mean 3.704→2.267 usec/op（约 38.8% 提升）；median 3.709→2.264（约 39.0%）。
- taskset -c 78,79：mean 3.621→2.255（约 37.7%）；median 3.558→2.261（约 36.5%）。

## 我可以参与的点
- review：复核 v6 的 `in_task()` 守卫与 `reciprocal_wakeup` 先捕获语义是否消除 Peter 指出的 `last_wakee` 不稳定问题。
- testing：在非 SMT 平台复现 `perf bench sched pipe` 数据，或在 SMT/异步容量平台上验证其对既有路径无回归（作者声明 SMT 仍走 select_idle_sibling）。

## 参考链接
- v6 lore：https://lore.kernel.org/all/20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org/
- v5 lore：https://lore.kernel.org/all/20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org/
