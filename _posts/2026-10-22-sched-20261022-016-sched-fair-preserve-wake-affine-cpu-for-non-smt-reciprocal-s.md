---
id: sched-20261022-016
date: 2026-10-22
subject: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261021-b4-sched-sync-wakeup-v7-1-91995ba5b596@gentwo.org>
lore_url: https://lore.kernel.org/all/20261021-b4-sched-sync-wakeup-v7-1-91995ba5b596@gentwo.org/
authors:
- Shubhang Kaushik
maintainers_involved: []
current_version: v7
patch_series:
- version: v7
  msgid: <20261021-b4-sched-sync-wakeup-v7-1-91995ba5b596@gentwo.org>
  date: 2026-10-22
  summary: 先记录 wakee 再测 reciprocal，显式要求双向 history 成立
  review_outcome: 当日无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - Peter 是否认可 v7 成对判定未可知
  next_action: 等待 Peter / 维护者 review v7
contribution_opportunities:
- kind: review
  description: 审读 v7 双向 reciprocal 判定是否服务 Peter 的可读性顾虑
- kind: testing
  description: 在非 SMT / 不对称容量平台跑 pipe ping-pong 验证
generated_at: '2026-10-23T01:20:00'
source_email_count: 1
related_articles:
- sched-20261013-015
tags:
- cfs
title: 'sched/fair: Preserve wake-affine CPU for non-SMT reciprocal sync wakeups'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-005-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261009-005</a>：Shubhang Kaushik（Ampere）发 v5——narrow reciprocal 的 `WF_SYNC` 唤醒在非 SMT 系统上保住在 wake-affine 选中的 waker CPU，不被 `select_idle_sibling()` 搬走；perf bench sched pipe mean 3.651→2.204（约 39.6%）。
- <a class="article-ref" href="/lkm/2026/10/12/sched-20261012-021-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261012-021</a>：Peter Zijlstra 强烈吐槽——代码难懂、!SMT 动机不清晰、`record_wakee()` 缺 `in_task()` 守卫，要求「用可读代码说服我」。
- <a class="article-ref" href="/lkm/2026/10/13/sched-20261013-015-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261013-015</a>：Shubhang 发 v6 逐条回应——`record_wakee()` 加 `in_task()` 守卫、`p->last_wakee == current` 在 `record_wakee()` 前捕获为局部布尔 `reciprocal_wakeup`、非 SMT 限制显式化；刷新 80 核非 SMT Ampere Altra 数据（mean 3.704→2.267，约 38.8%）。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-016-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261022-016</a>（今天）：作者发 v7——在测试 reciprocal 关系**之前**先记录 wakee，并显式要求 current↔wakee 双向 history 都成立，使 reciprocal handoff 在放置决策点可见；刷新 perf bench sched pipe 数据（mean 4.030→2.366，约 41.3%；taskset 78,79 mean 4.200→2.348，约 44.1%）。当日无回帖。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/10/09/sched-20261009-005-sched-fair-preserve-wake-affine-cpu-for-non-smt-reciprocal-s.html">sched-20261009-005</a>）`WF_SYNC` 唤醒下 `wake_affine()` 可能选中/保持 waker CPU，但后续 `select_idle_sibling()` 的空闲搜索可能把 wakee 搬走。pipe 式 ping-pong（A 唤醒 B、B 唤醒 A 循环）负载下，保住 wake-affine 的 waker CPU 比另找空闲 CPU 更有利。此前 v5 被 Peter 批评「函数大谈 sync-pair 却未真正确保成对、逻辑隐晦」，v6 已补 `in_task()` 守卫与局部布尔捕获。今日 v7 继续回应「成对可见性」。

## 技术方案
（承接 v6）v7（`kernel/sched/fair.c` +33）：`record_wakee()` 仍以 `if (!in_task()) return;` 开头；把 wakee 记录放在测试 reciprocal 关系**之前**；并显式要求 `p->last_wakee == current` 且 current↔wakee 双向 history 都成立才认定 reciprocal handoff，再经 `can_stack_on_waker()`（`rq->nr_running - cfs_h_nr_delayed(rq) == 1` 且不对称容量下 `task_fits_cpu()`）判定，命中则直接在非 SMT 上返回 waker CPU。SMT 与通用 `WF_SYNC` 仍走既有路径。

## 版本演进与当前进展
*current_version: v7*（`<20261021-b4-sched-sync-wakeup-v7-1-91995ba5b596@gentwo.org>`）。v6: `<20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org>`，v5: `<20261008-b4-sched-sync-wakeup-v5-1-1af9fab48965@gentwo.org>`。当日无回帖。

## Maintainer 意见与讨论焦点
当日无新 review；此前 Peter Zijlstra 的核心诉求（代码可读性、!SMT 动机、`record_wakee()` 的 `in_task()` 守卫、成对判定）已在 v6/v7 逐条回应，但仍未见 Peter 表态是否满意。

## 合入评估
*likelihood=medium*。v7 继续回应 Peter 的可读性诉求且数据良好，但主维护者尚未给出认可；*blocking_issues*：Peter 是否接受「成对可见性」的最终实现未可知；*next_action*：等待 Peter / 维护者 review v7。

## 效果评估
v7 刷新数据（80 核非 SMT Ampere Altra，`perf bench sched pipe -l 1000000` 30 轮，baseline a804c5742bff）：默认 mean 4.030→2.366 usec/op（约 41.3%）、median 4.110→2.334（约 43.2%）；`taskset -c 78,79` mean 4.200→2.348（约 44.1%）、median 4.294→2.316（约 46.1%）。

## 我可以参与的点
- *kind: review*：审读 v7 的双向 reciprocal 判定是否在保持可读性的同时覆盖了 Peter 的顾虑。
- *kind: testing*：在其它非 SMT 平台（尤其不对称容量拓扑）跑 pipe 式 ping-pong 验证。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261021-b4-sched-sync-wakeup-v7-1-91995ba5b596@gentwo.org/
- v6: https://lore.kernel.org/all/20261012-b4-sched-sync-wakeup-v6-1-aa70cde14463@gentwo.org/
