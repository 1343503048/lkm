# sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-006：李坤宇（Li kunyu）的补丁在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时改用「分布」策略把突发唤醒任务导流到其它 CPU；Kayra Cizmeci 与 K Prateek Nayak 给出密集意见（补丁甚至不适用于 mainline），作者逐条消化中。
- sched-20261106-004（今天）：**v2 发出**——rebase 到最新 mainline（Kayra），把 3x 阈值预计算并缓存在 root_domain、仅在变化时 WRITE_ONCE（K Prateek Nayak），在 domain 遍历前先查 `rq_burst_overloaded()`（KPN），改用 `rq->next_balance` 加 `time_after()` 门控提前触发周期均衡而非每次 wakeup 都遍历 domain（KPN、Kayra）。同时按 Kayra 意见把 `reset_periodic_lb_interval()` 改作用于真正被选中的 `dist_cpu`（而非输掉的 `new_cpu`），并简化实现。

## 背景与问题

（承接 sched-20261105-006）任务在 burst 唤醒场景下容易集中落在同一 runqueue，即使系统里有 idle CPU。作者目标是在 `select_task_rq_fair()` 唤醒路径里用「runqueue 深度达到平均深度 3 倍」作为过载信号，把唤醒任务分散，降低等待延迟。v1 的主要问题是实现细节与 reviewer 的期望不符（不适用于 mainline、每次 wakeup 遍历 domain 太重）。

## 技术方案

（承接 sched-20261105-006）v2 的落地形态：

- 顶层 domain 的周期负载均衡阶段，计算并缓存「3x 平均 runqueue 深度阈值」（下限 3 个任务）到 `root_domain->overload_nr_threshold`，仅在值变化时 `WRITE_ONCE`，避免热路径上的数学运算与 cacheline 污染。
- `select_task_rq_fair()` 里在扫描 domain/兄弟之前先查 `rq_burst_overloaded()`（`nr_running >= 阈值`）；命中时回退 `cpumask_any_and_distribute(p->cpus_ptr, cpu_active_mask)` 轮转分发唤醒任务（前提是目标队列深度更小），并提前 `rq->next_balance` 加速下一次周期均衡。
- `reset_periodic_lb_interval()` 从 v1 的「重置 `sd->balance_interval`」简化为只提前 `next_balance`（`time_after` 门控），且作用于 `dist_cpu`（真正返回的 CPU）而非输掉的 `new_cpu`——这是 Kayra 的修正意见（没被选中的 CPU 本就更忙，重置它的间隔没有意义）。

## 版本演进与当前进展

*current_version: v2（2026-11-06 发出，msgid 20261106062623.278004-1）*。当日 Kayra 在 v1 线程上指出 `reset_periodic_lb_interval()` 作用于 `new_cpu` 而非 `dist_cpu` 的问题，作者回帖确认已改为 `dist_cpu` 并简化实现，随后发出 v2。v2 的四处改动均回应了 K Prateek Nayak 与 Kayra 的意见。

## Maintainer 意见与讨论焦点

两位资深 reviewer 的意见主导了 v2 的成型：K Prateek Nayak 要求避免热路径数学（→缓存阈值）、domain 遍历前先判定过载（→`rq_burst_overloaded()` 前置）、用 `next_balance` 门控替代每次 wakeup 遍历 domain；Kayra 要求 rebase 到 mainline 并纠正 `reset_periodic_lb_interval()` 的作用对象。未出现 NAK，但也没有维护者表态接收。

## 合入评估

*likelihood=low*。v2 已逐条响应 reviewer 意见、rebase 到 mainline，但该机制触及 wakeup 热路径，且此前 reviewer 明确指出 v1「不适用于 mainline」，仍需 K Prateek Nayak/Kayra 对 v2 的重新确认与实测数据。*blocking_issues*：① 尚无 v2 的 reviewer 再确认；② 缺性能数据说明「分布策略」相对现状的实际收益。*next_action*：作者补充 benchmark 数据、等待 reviewer 对 v2 的复审。

## 效果评估

暂无效果数据。作者在 v1 讨论中提到「昨天的测试表明这一改动可以进一步优化、影响不显著」，未给出具体数字；分布策略的收益为作者主观判断，未见测试数据。

## 我可以参与的点

- **testing**：在突发唤醒（burst wakeup）负载下实测 v2 的延迟收益与热路径开销——作者缺数据，这是最直接的参与点。
- **review**：复核 `rq_burst_overloaded()` 阈值缓存与 `reset_periodic_lb_interval()` 对 `next_balance` 的提前触发是否引入周期性均衡抖动。

## 参考链接

- lore thread（v2）: https://lore.kernel.org/all/20261106062623.278004-1-likunyu@open-hieco.net/
- v1 文章: sched-20261105-006（见 sched/2026/11/ 归档）

---
id: sched-20261106-004
date: 2026-11-06
subject: "sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261106062623.278004-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/20261106062623.278004-1-likunyu@open-hieco.net/"
authors: [Li kunyu]
maintainers_involved: []
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261104091842.266273-1-likunyu@open-hieco.net>"
    date: 2026-11-04
    summary: "wakeup 路径按 3x 平均深度阈值分布突发唤醒任务。"
    review_outcome: "Kayra/K Prateek Nayak 密集意见（不适用 mainline、热路径过重）。"
  - version: v2
    msgid: "<20261106062623.278004-1-likunyu@open-hieco.net>"
    date: 2026-11-06
    summary: "rebase mainline，缓存 3x 阈值，domain 遍历前判定，next_balance 门控提前均衡，reset 作用于 dist_cpu。"
    review_outcome: "响应 KPN/Kayra 意见，尚无 reviewer 再确认。"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - "尚无 v2 的 reviewer 再确认"
    - "缺性能数据说明分布策略的实际收益"
  next_action: "作者补充 benchmark 数据并等待 reviewer 复审"
contribution_opportunities:
  - kind: testing
    description: "在 burst wakeup 负载下实测 v2 延迟收益与热路径开销"
  - kind: review
    description: "复核阈值缓存与 next_balance 提前触发是否引入均衡抖动"
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 4
related_articles: [sched-20261105-006]
tags: [cfs, load_balance]
---