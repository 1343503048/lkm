---
id: sched-20260729-005
date: 2026-07-29
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260723040429.630176-1-luogengkun2@huawei.com>
lore_url: https://lore.kernel.org/r/20260723040429.630176-1-luogengkun2@huawei.com
authors:
- Luo Gengkun
maintainers_involved:
- Tim Chen
- Chen Yu
current_version: v8
patch_series:
- version: v8
  msgid: <20260723040429.630176-1-luogengkun2@huawei.com>
  date: 2026-07-23
  summary: task_cache_work() 只扫描进程实际访问过的 CPU（visited cpus）而非全部 CPU，降低 cache-aware
    调度的扫描开销（v1-v7 演进未在当日缓存内）。
  review_outcome: Tim Chen 给出 Reviewed-by；Luo 提出相邻扫描周期并发执行的边界场景，Chen Yu 认为可容忍，建议下版只改注释表述。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 相邻 epoch 并发扫描的边界场景达成'可容忍'共识，但需在下一版落实注释修改
  next_action: 作者按 Chen Yu 建议更新注释（'elect a single scanner per epoch'）发 v9，或维护者直接收
    v8
contribution_opportunities:
- kind: review
  description: 并发场景分析仍开放：可独立审视 try_cmpxchg 选举窗口下两个 task_cache_work 重叠执行时 cpumask_clear
    的实际影响，验证'可容忍'结论
generated_at: '2026-07-30T09:30:00'
source_email_count: 3
related_articles: []
tags:
- cfs
- perf
title: ': [PATCH v8 1/2] sched/cache: Reduce the overhead of task_cache_work by only
  scan the visisted cpus'
layout: article
---

## TL;DR

cache-aware 调度系列中的扫描开销优化（`task_cache_work()` 只扫 visited cpus）走到 v8，Tim Chen 给了 Reviewed-by；剩余讨论集中在一个罕见并发场景是否需要显式互斥，Chen Yu 判定可容忍、只需改注释。接近成熟。

## 背景与问题

cache-aware 调度（sched/cache）需要周期性扫描 CPU 统计任务的 cache 占用。`task_cache_work()` 原来扫描全部 CPU，在大机器上开销明显。该系列（v8 1/2，华为 Luo Gengkun）改为只扫描进程实际运行过的 CPU 集合。v1-v7 的演进历史不在当日邮件缓存内。

## 技术方案

维护进程访问过的 CPU 位图，`task_cache_work()` 只遍历该位图。扫描者选举用 `try_cmpxchg` 更新 `next_scan` 时间戳实现"每个周期一个扫描者"。

## 版本演进与当前进展

v8。当日进展：Tim Chen（Intel）review 通过；作者 Luo 自己提出一个边界场景——线程 A 在扫描循环中被抢占拖过一个扫描周期，线程 B 通过 `next_scan` 超时检查后 `try_cmpxchg` 成功，两个相邻周期的 `task_cache_work()` 并发执行，是否需要 `test_and_set_bit` 显式状态位保证前一次扫描完全结束。

## Maintainer 意见与讨论焦点

- **Tim Chen**：代码 OK，Reviewed-by。
- **Chen Yu（Intel，sched/cache 方向主导者）**：并发场景成立但可容忍——`account_mm_sched()` 并发加位丢失可接受，`fraction_mm_sched()` 重复 `cpumask_clear()` 也可容忍；建议把注释从 "only 1 thread is allowed to scan" 改为 "elect a single scanner per epoch"，如实反映语义。
- 分歧点：是否需要显式互斥。当前结论是"不需要，改注释即可"，但这是基于"罕见+影响可容忍"的判断，不是硬性证明。

## 合入评估

likelihood: medium。review 基本通过，但 sched/cache 整个方向仍在迭代中（已到 v8），该 patch 的合入节奏取决于整个系列的推进。下一步动作明确：按建议改注释。

## 效果评估

当日邮件未包含扫描开销的具体对比数字（应在 cover letter/早期版本中，未获取到）。

## 我可以参与的点

- 并发正确性验证：构造高抢占场景（大量 CPU + 长扫描 + 强制抢占）验证相邻 epoch 并发扫描的实际影响，为"可容忍"结论补实证。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260723040429.630176-1-luogengkun2@huawei.com
