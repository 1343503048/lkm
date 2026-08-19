# sched/core: Skip rq->avg_idle update without a valid idle_stamp

## TL;DR

Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。

## 背景与问题

Commit 4b603f1551a73 把 `rq->avg_idle` 的更新从 wakeup 路径挪到 `put_prev_task_idle()`。旧的 wakeup 侧代码只在 `rq->idle_stamp` 非零时才更新；新 helper 丢了这个检查，无条件计算 `rq_clock(rq) - rq->idle_stamp`。当 `idle_stamp==0`（未经过 newidle balance 的 idle 切换，如 `find_proxy_task()` 的 proxy idle、force-idle）时，样本变成 rq_clock 的绝对值，立即把 avg_idle 推到 `2*max_idle_balance_cost` 的 clamp。avg_idle 直接影响 newidle balance 的激进程度，被污染后行为失真。

作者用 hackbench 负载下的临时 tracing 确认了 `idle_stamp==0` 时确实会走到 `update_rq_avg_idle()`。

## 技术方案

在 `update_rq_avg_idle()` 开头加 `if (unlikely(!idle_stamp)) return;`，无有效 idle 区间就不更新。作者说明这是早前一个提案（firelzrd 的讨论）的收窄版本：保留 guard 但故意不在 `set_next_task_idle()` 打 idle 时间戳，避免把 forced/proxy idle 也计入统计。

## 版本演进与当前进展

v1，已获 K Prateek Nayak 的 Reviewed-by。

## Maintainer 意见与讨论焦点

Prateek 确认了触发场景的合理性（proxy execution 的 `find_proxy_task()` 和 force-idling 会在没有 newidle balance 的情况下切到 idle 上下文），并抄送 John（proxy execution 作者）知会。无分歧。

## 合入评估

likelihood: high。语义上是恢复被重构丢掉的原有检查，带 Fixes 标签 + Reviewed-by，改动小且动机清楚。

## 效果评估

- 作者：hackbench 相对 v7.2-rc5 主线"无实质回退"（修复本身是正确性修复，不追求性能收益）
- 污染场景的量化影响（newidle balance 频率变化）暂无数据

## 我可以参与的点

- 可以做一个量化实验：对比补丁前后 avg_idle 命中 clamp 的频率与 newidle balance 触发次数（schedstat / tracepoint），把数据回帖，能加强合入依据。

## 参考链接

- lore thread: https://lore.kernel.org/r/20260728-master-v1-1-f95d9b0147d2@gentwo.org
- 早前相关讨论: https://lore.kernel.org/r/20260423023322.1293923-1-firelzrd@gmail.com

---
subject: "sched/core: Skip rq->avg_idle update without a valid idle_stamp"
id: sched-20260729-004
date: 2026-07-29
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260728-master-v1-1-f95d9b0147d2@gentwo.org>"
lore_url: "https://lore.kernel.org/r/20260728-master-v1-1-f95d9b0147d2@gentwo.org"
authors: [Shubhang Kaushik]
maintainers_involved: [K Prateek Nayak]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20260728-master-v1-1-f95d9b0147d2@gentwo.org>"
    date: 2026-07-29
    summary: "update_rq_avg_idle() 恢复 idle_stamp 有效性检查：idle_stamp 为 0 时跳过 avg_idle 更新，避免用 rq_clock 整值污染 avg_idle。"
    review_outcome: "Prateek 给出 Reviewed-by，并确认 proxy execution / force-idle 路径确实会触发 idle_stamp==0 的情况。"
upstream_commit: null
fixes_commit: "4b603f1551a73"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "带 Prateek 的 Reviewed-by 等待维护者收取，或视意见发 v2"
contribution_opportunities:
  - kind: testing
    description: "在 newidle balance 敏感的负载（hackbench/schbench）上验证 avg_idle 被污染前后 newidle balance 触发频率的差异，补充量化数据"
generated_at: "2026-07-30T09:30:00"
source_email_count: 2
related_articles: []
tags: [cfs, load_balance, idle]
---
