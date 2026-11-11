# sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261105-006：李坤宇（Li kunyu）的补丁在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时改用「分布」策略把突发唤醒任务导流到其它 CPU；Kayra Cizmeci 与 K Prateek Nayak 给密集意见（补丁甚至不适用于 mainline）。
- sched-20261106-004：v2 发出——rebase 到最新 mainline、3x 阈值预计算缓存进 root_domain、改用 `rq->next_balance` 门控提前触发周期均衡。
- sched-20261109-008：v3 发出，附完整 benchmark：整体平均 +12.44%；作者透露 READ_ONCE 形式导致 >3% 回退，v3 已从热点函数移除 READ_ONCE/WRITE_ONCE。
- sched-20261111-013（今天）：**v4 发出并附一组新 benchmark**——整体平均 +8.99%（hackbench +8.59%、tbench +6.48%、schbench 99th +3.93%、stream-10 +16.15%、stream-100 +18.28%、unixbench +0.54%）。v4 按 Kayra 意见：调度域间隔复位收敛到 `time_after()` 条件块内、只在 `env->cpus` 有完整 CPU 统计时更新阈值、用 `housekeeping_cpumask(HK_TYPE_DOMAIN)` 过滤隔离 CPU。

## 背景与问题

（承接 sched-20261105-006 / 20261106-004 / 20261109-008）任务突发唤醒大量任务时，短时间内容易堆叠到同一 CPU——即使系统有 idle CPU 或启用了 NO_HZ 也不一定疏散。作者希望在 wakeup 路径上、当目标 runqueue 深度达到平均 nr_running 的 3 倍时改用「分布」策略，把突发唤醒的任务轮转导流到允许的非隔离 CPU，避免单 CPU 堆积。

## 技术方案

v4 核心设计（承接 v2/v3）：顶层域周期负载均衡时计算并缓存 3x 平均 runqueue 深度阈值（下限 3 任务）到 root_domain，仅在值变化时更新；`select_task_rq_fair()` 里检查醒来的目标 CPU 深度是否达阈值，达阈值则 `cpumask_any_and_distribute()` 轮转导流到队列更短的非隔离 CPU，并拉近 `rq->next_balance`、把 `balance_interval` 复位到 `min_interval` 以便周期均衡尽快抹平分布。v4 相对 v3：调度域间隔复位放进 `time_after()` 条件块；只在 `env->cpus` 具备完整 CPU 统计时更新 `overload_nr_threshold`；隔离 CPU 经 `housekeeping_cpumask(HK_TYPE_DOMAIN)` 过滤。

## 版本演进与当前进展

*current_version: v4（2026-11-11，`<20261111061803.337042-1-likunyu@open-hieco.net>`）*。v4 落实 Kayra 三项意见（间隔复位条件、阈值更新时机、隔离 CPU 过滤），并同步更新 commit message 与一组新 benchmark。当日无新 review 回复（作者在补测数据回帖中致谢维护者）。

## Maintainer 意见与讨论焦点

- 采纳的既有评审（v2/v3 阶段）：Kayra Cizmeci 的阈值更新时机与复位条件、隔离 CPU 过滤；K Prateek Nayak 的热点函数移除 READ_ONCE/WRITE_ONCE、缓存 3x 阈值。
- 当日无新分歧。系列属「作者按评审迭代 + 补数据」的正常推进节奏。

## 合入评估

*likelihood=medium*。作者响应积极、benchmark 完整，但方案本身（在 wakeup 路径按 3x 平均深度做分布导流）仍属启发式设计，且主要反馈来自 reviewer 而非 sched 维护者本人；schbench 99th 在部分线程数（64/128）仍有 -9.51%/-1.19% 的回退。*blocking_issues*：需要 sched/fair 维护者对「wakeup 路径引入分布导流」这一方向本身的认可。*next_action*：等 Peter/Vincent 等维护者表态；或就 schbench 高线程数回退做进一步分析。

## 效果评估

v4 benchmark（对比 baseline，正值=改善）：整体平均 +8.99%；hackbench +8.59%（g16 +16.51%、g32 +16.45%，但 g1/g2 有 -3.73%/-5.95%）；tbench +6.48%（256 clients +41.49%，64/128 有 -2.44%/-3.47%）；schbench 99th +3.93%（128 threads -9.51%）；stream-10 +16.15%、stream-100 +18.28%；unixbench +0.54%。存在个别高并发档位的回退。

## 我可以参与的点

- **testing**：针对性跑 schbench 64/128 线程档，分析 v4 在这些点上的回退是否可复现、是否与分布导流的阈值选择有关，并回帖数据。
- **review**：复合核/迁移禁用任务与 `cpumask_any_and_distribute()` + `housekeeping_cpumask` 的交互是否正确。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261111061803.337042-1-likunyu@open-hieco.net/
- v4 的 benchmark 回帖: https://lore.kernel.org/all/b7635a7c-ebda-212f-575a-6d282997210f@open-hieco.net/

---
id: sched-20261111-013
date: '2026-11-11'
subject: "sched/fair: Distribute burst-woken tasks when rq depth reaches 3x average"
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: "<20261111061803.337042-1-likunyu@open-hieco.net>"
lore_url: "https://lore.kernel.org/all/20261111061803.337042-1-likunyu@open-hieco.net/"
authors: [Li kunyu]
maintainers_involved: []
current_version: v4
patch_series:
  - version: v4
    msgid: "<20261111061803.337042-1-likunyu@open-hieco.net>"
    date: '2026-11-11'
    summary: "间隔复位进 time_after 块、阈值更新时机、housekeeping 过滤隔离 CPU"
    review_outcome: "落实 Kayra 三项意见；等维护者表态"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: ["需 sched/fair 维护者对 wakeup 路径分布导流方向本身认可"]
  next_action: "等维护者表态，或分析 schbench 高线程数回退"
contribution_opportunities:
  - kind: testing
    description: "复测 schbench 64/128 线程档的回退并回帖分析"
  - kind: review
    description: "复核 cpumask_any_and_distribute + housekeeping_cpumask 与迁移禁用任务的交互"
generated_at: "2026-11-12T09:00:00+08:00"
source_email_count: 2
related_articles: [sched-20261105-006, sched-20261106-004, sched-20261109-008]
tags: [load_balance, cfs]
---