# sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-006：李坤宇（Li kunyu）的补丁在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时改用「分布」策略把突发唤醒任务导流到其它 CPU；Kayra Cizmeci 与 K Prateek Nayak 给出密集意见（补丁甚至不适用于 mainline），作者逐条消化中。
- sched-20261106-004：v2 发出——rebase 到最新 mainline、3x 阈值预计算缓存进 root_domain、改用 `rq->next_balance` 门控提前触发周期均衡等。
- sched-20261109-008（今天）：**v3 发出**，并附完整 benchmark：整体平均 **+12.44%**（hackbench +9.26%、tbench +9.71%、stream-100 +51.5%、unixbench -0.89%、schbench 99th -1.33%）；作者透露 READ_ONCE 形式导致 >3% 回退，v3 已从热点函数移除 READ_ONCE/WRITE_ONCE。

## 背景与问题

（承接 sched-20261105-006 / 20261106-004）任务突发唤醒大量任务时，短时间内容易堆叠到同一 CPU——即使系统有 idle CPU 或启用了 NO_HZ 也不一定疏散。作者希望在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时改用「分布」策略，把突发唤醒的任务轮转导流到允许的 CPU，避免单 CPU 堆积。

## 技术方案

v3 的核心设计（承接 v2）：在顶层域周期负载均衡时计算并缓存 3x 平均 runqueue 深度阈值（下限 3 个任务）到 root_domain，仅在值变化时更新；`select_task_rq_fair()` 里在扫域/扫兄弟之前检查醒来的 CPU 深度是否达阈值，达阈值则 `cpumask_any_and_distribute()` 轮转导流（目标队列更短时），并拉近 `rq->next_balance` 提前下一次周期均衡。v3 相对 v2 的关键变化：从热点函数移除 READ_ONCE/WRITE_ONCE 避免过度开销；把过载检查移到 `select_task_rq_fair()` 末尾、只作用于最终的任务疏散效果。作者实测 READ_ONCE 形式整体回退 >3%，故移除。

## 版本演进与当前进展

*current_version: v3（2026-11-09，`<20261109083530.328796-1-likunyu@open-hieco.net>`）*。v3 今日发出（Suggested-by Peter Zijlstra，Link 指向 Peter 的负载均衡思路帖）。作者附完整 benchmark 并解释 v3 相对 v2 的两处改动动机。

## Maintainer 意见与讨论焦点

今日无维护者回帖（作者自我验证帖占主导）。此前（v1/v2）Kayra Cizmeci、K Prateek Nayak 曾给出密集意见——已被 v2/v3 逐条消化（rebase mainline、阈值缓存、`next_balance` 门控、`reset_periodic_lb_interval()` 作用于选中 CPU）。Peter Zijlstra 以 Suggested-by 背书思路方向。当前无 NAK。

## 合入评估

*likelihood=medium*。作者已按两位资深 reviewer 意见迭代到 v3 并给出详实 benchmark，但今日无新评审，且改动落在 `select_task_rq_fair()` 热路径，需维护者确认开销/收益权衡。*blocking_issues*：① v3 尚未获维护者评审；② 热路径引入的深度检查开销需被认可。*next_action*：等 Kayra/KPN/Peter 对 v3 的评审。

## 效果评估

作者自测（238214）：整体平均 +12.44%，hackbench +9.26%（-g 8/16/32/64 提升 10-18%，-g 2 回退 -10.44%）、tbench +9.71%（128 clients -12.7%、256 +47.2%、1024 +30.8% 波动较大）、stream-100 +51.5%、stream-10 +6.36%、schbench 99th -1.33%、unixbench -0.89%。README_ONCE 形式整体回退 >3%（故 v3 移除）。数据为作者自测，未见第三方独立复现。

## 我可以参与的点

- **testing**：独立复现 v3 的 benchmark（尤其 tbench 128 clients 的 -12.7% 与 hackbench -g 2 的 -10.44% 回退点），验证是否随波动。
- **review**：审查 `cpumask_any_and_distribute()` 与 `rq->next_balance` 门控在 NO_HZ 与 idle CPU 场景的语义正确性。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261109083530.328796-1-likunyu@open-hieco.net/
- benchmark 回帖: https://lore.kernel.org/all/56803cce-a01f-8234-ff33-59b0616c6eb1@open-hieco.net/

---
id: sched-20261109-008
date: '2026-11-09'
subject: "sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261109083530.328796-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/20261109083530.328796-1-likunyu@open-hieco.net/"
authors: [Li kunyu]
maintainers_involved: []
current_version: v3
patch_series:
  - version: v3
    msgid: "<20261109083530.328796-1-likunyu@open-hieco.net>"
    date: '2026-11-09'
    summary: "从热点移除 READ_ONCE/WRITE_ONCE、过载检查移到函数末尾只作用于疏散"
    review_outcome: "作者自测整体 +12.44%，README_ONCE 形式回退 >3% 故移除"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "v3 尚未获维护者评审"
    - "热路径开销需被认可"
  next_action: "等 Kayra/KPN/Peter 对 v3 的评审"
contribution_opportunities:
  - kind: testing
    description: "独立复现 v3 benchmark，验证 tbench 128 clients 与 hackbench -g 2 的回退点是否随波动"
  - kind: review
    description: "审查 cpumask_any_and_distribute 与 next_balance 门控在 NO_HZ/idle 场景语义"
generated_at: "2026-11-10T09:00:00+08:00"
source_email_count: 3
related_articles: [sched-20261105-006, sched-20261106-004]
tags: [load_balance, cfs, nohz]
---