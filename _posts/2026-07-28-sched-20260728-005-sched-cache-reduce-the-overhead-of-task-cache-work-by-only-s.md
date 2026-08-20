---
subject: ': [PATCH v8 1/2] sched/cache: Reduce the overhead of task_cache_work by
  only scan the visisted cpus'
id: sched-20260728-005
date: 2026-07-28
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com>
lore_url: https://lore.kernel.org/r/cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com
authors:
- Zhan Xusheng
maintainers_involved:
- Tim Chen
current_version: v8
patch_series:
- version: v8
  msgid: <cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com>
  date: 2026-07-27
  summary: Use for_each_cpu_and with visited_cpus to only scan visited CPUs in task_cache_work,
    removing get_scan_cpumasks()
  review_outcome: 华为开发者提出并发安全疑问；Chenyu 确认 try_cmpxchg 保证单 scanner
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 并发安全性讨论仍在进行
  - 需要 Tim Chen 最终确认
  next_action: 解决并发安全疑问后等待 Tim Chen 最终 review
contribution_opportunities:
- kind: testing
  description: 在多核系统上测试 task_cache_work 优化后的 cache 亲和性效果和开销变化
generated_at: '2026-07-30T10:00:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- perf
title: ': [PATCH v8 1/2] sched/cache: Reduce the overhead of task_cache_work by only
  scan the visisted cpus'
layout: article
---

## TL;DR

sched/cache 的 task_cache_work 优化补丁（v8）进入深度技术讨论阶段。华为开发者质疑 `visited_cpus` 在扫描期间被并发清除的风险，Chenyu 回复确认 `try_cmpxchg` 已保证同一 mm 同一时刻只有一个 scanner。讨论趋于收敛。

## 背景与问题

`task_cache_work()` 在每个 scan period 遍历所有 CPU 检查 cache 亲和性统计，在大核数系统上开销显著。本系列通过只扫描实际被访问过的 CPU（`visited_cpus` bitmap）来减少无效遍历。

## 技术方案

- 用 `for_each_cpu_and(i, sched_domain_span(sd), &mm->sc_stat.visited_cpus)` 替代全量 `for_each_cpu`
- 移除 `get_scan_cpumasks()` 辅助函数
- `visited_cpus` 的清除只在 `task_cache_work()` 中发生（每个 scan period 一次）

## 版本演进与当前进展

v8 是当前版本。本次邮件是 review 讨论：

1. **华为开发者**（uid=4892，`@huawei.com`）提出疑问：
   - v2 中 `for_each_cpu` 需要 `cpumask_test_cpu` 过滤，v8 用 `for_each_cpu_and` 后不再需要
   - 但质疑：如果当前 `task_cache_work()` 被中断/抢占延迟，下一个 scan window 到来时 `visited_cpus` 是否会被并发清除？
   - 建议：将 `work->next = work;` 移到 `task_cache_work()` 末尾，让 `task_tick_cache()` 中的 `work->next == work` 检查阻止重复提交

2. **Chenyu**（uid=5269）回复确认：
   > "There are two layers of protection: first a cheap timeout gate (time_before) that skips scanning until the next period, and then a try_cmpxchg that atomically picks a single winner among the threads that pass the timeout — this actually guarantees only one scanner per mm at a time, no?"

## Maintainer 意见与讨论焦点

- Tim Chen（Intel）此前参与了 review，本次邮件中未直接发言
- 华为开发者的并发安全疑问是核心技术争议点
- Chenyu 的解释（time_before + try_cmpxchg 双重保护）如果成立，则该疑问已解决

## 合入评估

可能性中等。v8 已经迭代多版，技术方向基本确定。当前阻塞在于并发安全讨论是否完全收敛，以及 Tim Chen 是否给出最终确认。

## 效果评估

华为开发者提到：

> "I believe that the results are likely due to run-to-run variance."

暗示此前某些测试结果可能是噪声。具体性能数据未在本次邮件中给出。

## 我可以参与的点

- **测试**：在多核系统（64+ 核）上对比 v8 前后的 task_cache_work 开销（通过 perf 采样 `task_cache_work` 占比），以及 cache miss rate 变化
- 如果对并发安全分析有见解，可以参与讨论确认 try_cmpxchg 的保护是否充分

## 参考链接

- lore thread: https://lore.kernel.org/r/cc9d6d06-382e-4f67-aaad-25e58fac90a1@intel.com
- tip-bot commit: 未获取到
