---
id: sched-20260731-006
date: 2026-07-31
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: <20260731024417.1106503-1-luogengkun2@huawei.com>
lore_url: https://lore.kernel.org/lkml/20260731024417.1106503-1-luogengkun2@huawei.com
authors:
- Luo Gengkun
maintainers_involved:
- Tim Chen
- Intel
current_version: v9
patch_series:
- version: v9
  msgid: <20260731024417.1106503-1-luogengkun2@huawei.com>
  date: 2026-07-31
  summary: 'v9: 仅扫描已访问 CPU 以减少 task_cache_work 开销；附带 debug trace event（标记 DO NOT APPLY）'
  review_outcome: Tim Chen 和 Chenyu 讨论 epoch 回退逻辑和锁获取时机
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - epoch 回退逻辑的正确性仍需确认
  - debug patch（2/2）标记为 DO NOT APPLY
  next_action: 等待更多 review 反馈，确认 epoch 逻辑无 race
contribution_opportunities: []
generated_at: '2026-07-31T16:30:00'
source_email_count: 4
related_articles:
- sched-20260730-010
tags:
- cfs
- load_balance
- sched_debug
title: '-- DO NOT APPLY!!! -- sched/cache/debug: Add trace event and sched feature
  to track scan cost'
layout: article
---

## TL;DR

本文为增量更新，完整背景见 sched-20260730-010。Luo Gengkun (Huawei) 的 cache-aware 调度补丁系列推进到 v9，核心优化是 task_cache_work 仅扫描已访问 CPU 以减少开销。v9 新增讨论焦点：Tim Chen 和 Chenyu 就 epoch 回退逻辑的正确性和锁获取时机展开讨论。

## 背景与问题

（完整背景见 sched-20260730-010）task_cache_work 在每个调度周期扫描所有 CPU 的缓存状态，即使大部分 CPU 的缓存亲和性信息未变化，造成不必要的开销。v9 通过仅扫描自上次以来被访问过的 CPU 来减少开销。

## 技术方案

v9 核心变更：
- 仅扫描已访问的 CPU（visited cpus），减少 task_cache_work 的扫描范围
- 附带 debug trace event 和 sched feature 用于跟踪扫描开销（Patch 2/2，标记为 "DO NOT APPLY"）

## 版本演进与当前进展

- **v9**（2026-07-31）：当前版本。讨论集中在 epoch 回退逻辑

## Maintainer 意见与讨论焦点

**Tim Chen (Intel)** 对 epoch 回退逻辑提出关注：

- v9 中 `__update_mm_sched()` 的 "avoid moving backwards" 逻辑最初在 commit df0d98475954 中引入，用于防止 epoch 差值为负导致超时计算错误
- 后续 commit c1e7fe5e75ed 改用 `(long)` 有符号比较处理负 delta，使得 epoch 回退不再导致计算错误
- Tim 认为 epoch 回退"不是大问题"，但仍需确认

**Chenyu** 回应：
- `__update_mm_sched()` 中 Thread A 会读取更新的 `rq->cpu_epoch` 并再次检查时间是否回退
- 不应在时间检查前获取锁，因为 `account_mm_sched()` 频繁调用，应避免不必要的锁获取

## 合入评估

- **likelihood: medium** — v9 已迭代多版，核心逻辑趋于稳定，但 epoch 正确性讨论仍在进行
- **blocking_issues**: epoch 回退逻辑的正确性需确认无 race
- **next_action**: 等待 Tim Chen 和其他 reviewer 对 epoch 讨论的最终确认

## 效果评估

暂无新的效果数据。

## 我可以参与的点

当前阶段暂无明显参与空间。epoch 逻辑讨论较为专业，需要深入理解 cache-aware 调度的实现细节。

## 参考链接

- lore thread: https://lore.kernel.org/lkml/20260731024417.1106503-1-luogengkun2@huawei.com
- 前日分析: sched-20260730-010
