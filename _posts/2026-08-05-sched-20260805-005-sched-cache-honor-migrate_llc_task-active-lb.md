---
id: sched-20260805-005
date: '2026-08-05'
title: 'sched/cache: honor migrate_llc_task semantics in active load balance'
series: Honor migrate_llc_task semantics in active load balance
type: fix
status: under_review
severity: medium
merge_likelihood: high
tags:
- cfs
- load_balance
- affinity
authors:
- Tim Chen <tim.c.chen@linux.intel.com>
- K Prateek Nayak <kprateeknayak@amd.com>
reviewers:
- K Prateek Nayak <kprateeknayak@amd.com>
- Peter Zijlstra <peterz@infradead.org>
related_articles:
- sched-20260804-007
emails:
- uid-21368@qq-imap
- uid-20828@qq-imap
layout: article
---

# sched/cache: active 负载均衡尊重 migrate_llc_task 语义

## 摘要

Tim Chen（Intel）的「在 active load balance 中尊重 `migrate_llc_task` 语义」系列在 08-05 推进（可见 v2 的 0/5 与具体 patch）。`migrate_llc_task` 是一个用于把任务限制在「最后运行 LLC 域内」的亲和性提示，目的是让缓存热任务不被搬到跨 LLC 的远处 CPU，从而保住 cache 命中率。

问题：active load balance（`active_load_balance_cpu_stop()`）在做「pull 一个任务到本地」时，没有检查目标任务的 `migrate_llc_task` 约束，可能把一个明确想留在原 LLC 的任务强行拉走，破坏作者的缓存局部性意图。

本日要点：
- **Tim 的覆盖说明**：v2 把「migrate_llc_task 检查」从 `can_migrate_task()` 扩展到 `active_load_balance_cpu_stop()` 路径，在 stopper 线程决定 pull 之前先确认目标任务允许离开其 LLC。
- **Prateek（AMD）的 review**：确认该检查与 `can_migrate_task()` 现有逻辑语义一致，不会与 `migrate_disable` / `cpu_active` 等既有约束冲突；同时建议把「被 migrate_llc_task 阻止而无法均衡」的情况在 `update_sd_lb_stats()` 的统计里显式计数，便于后续量化这类「因 cache 提示而放弃均衡」的频率。

## 技术细节

`migrate_llc_task` 意图：任务的 `cpus_mask` 正常情况下允许跨 LLC，但作者通过 `migrate_llc_task` 标记表达「除非必要，别让我离开当前 LLC」。active LB 的 stopper 路径此前绕过了这个提示。

修复点（示意）：
```
active_load_balance_cpu_stop():
    p = detach_one_task(...);
    if (p && task_wants_llc_stay(p) && !llc_match(src, dst))
        // 放弃这次 pull，放回原位
        goto out;
```

争议/关注点：
- stopper 线程运行在 `cpumask` 受限上下文，需要在持 `rq` 锁且 `p->pi_lock` 的情况下读取 `migrate_llc_task` 状态，注意与 `set_cpus_allowed` 的竞态。Prateek 建议在已有的 `task_rq_lock()` 区域内读取，复用现有保护。
- 是否需要为「被 LLC 约束挡掉的均衡」新增一个 `schedstat`，以便区分「均衡失败是因为忙」与「因为 cache 提示」。

## 影响与风险

- 影响面：active load balance 的 pull 决策，缓存热点任务（如某些 HPC / 数据库 worker）受益，避免跨 LLC 抖动。
- 风险：中。改动在 stopper 上下文，需确认不会引入新的迁移死锁或统计膨胀；但逻辑与既有 `can_migrate_task` 一致，风险可控。
- 收益：让 `migrate_llc_task` 这个 cache 提示在「被迫 active 均衡」时也真正生效，而非只在 normal LB 生效。

## 评价

方向合理、reviewer（Prateek）已确认语义一致，合入可能性高。建议采纳 Prateek 的 schedstat 计数建议，便于量化收益。
