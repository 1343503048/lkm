---
id: sched-20260806-008
date: "2026-08-06"
title: "sched/cache: active 负载均衡尊重 migrate_llc_task 语义（Chen Yu 备选方案）"
series: "Honor migrate_llc_task semantics in active load balance"
type: fix
status: under_review
severity: medium
merge_likelihood: medium
tags: [cfs, load_balance, affinity]
authors: ["Tim Chen <tim.c.chen@linux.intel.com>", "Lu Wang <wanglu.kerry@bytedance.com>", "Chen Yu <yu.c.chen@intel.com>", "K Prateek Nayak <kprateeknayak@amd.com>"]
reviewers: ["Chen Yu <yu.c.chen@intel.com>", "Prateek Nayak <kprateeknayak@amd.com>"]
related_articles: ["sched-20260805-005", "sched-20260804-007"]
emails: ["uid-24954@qq-imap", "uid-22937@qq-imap", "uid-22838@qq-imap"]
---

# sched/cache: active 负载均衡尊重 migrate_llc_task 语义（Chen Yu 备选方案）

## 摘要

Tim Chen 的「active load balance 尊重 `migrate_llc_task` 语义」系列（延续 08-05-005）在 08-06 收到 **Chen Yu（Intel）的 review**：他提出一个**备选实现路径**——不修改 `active_load_balance_cpu_stop()` 的 pull 决策，而是从 `can_migrate_task()` 的角度把 `migrate_llc_task` 约束统一表达，使得 normal LB 与 active LB 共用同一套「是否允许离 LLC」判定。

要点：
- Tim（24954 等）：坚持在 stopper 路径显式检查，因为 active LB 是唯一会「强行 pull」的路径，normal LB 已被 `can_migrate_task` 覆盖。
- Chen Yu：指出 `migrate_llc_task` 的「仅留本地 LLC」意图当前只在 `can_migrate_task` 里有部分表达，建议把它抽成 `task_wants_llc_stay()` 公共 helper，让两路径都调用，避免逻辑漂移；并补充一个 schedstat 计数「因 LLC 约束放弃的均衡次数」便于量化。
- Prateek（延续 08-05-005 的 review）：确认两种路径语义需一致，倾向 Chen Yu 的「统一 helper」方向，比在 stopper 里单独加分支更易维护。

## 技术细节

Chen Yu 建议的 helper（示意）：
```
bool task_wants_llc_stay(struct task_struct *p, int src_cpu, int dst_cpu)
{
    if (!task_has_migrate_llc_task(p)) return false;
    return cpuset_llc_id(src_cpu) != cpuset_llc_id(dst_cpu);
}
// can_migrate_task() 与 active_load_balance_cpu_stop() 都用它判定
```

Prateek 的 schedstat 建议：在 `update_sd_lb_stats()` 增加 `sgs->llc_blocked` 计数。

## 影响与风险

- 影响面：active / normal load balance 的 pull 决策，缓存热点任务（HPC / 数据库 worker）受益。
- 风险：中。两路径统一 helper 需确认不破坏既有 `can_migrate_task` 语义，且 stopper 持锁窗口读取 `migrate_llc_task` 需 `task_rq_lock()` 保护（延续 08-05-005 的关注点）。
- 收益：让 `migrate_llc_task` 在所有均衡路径真正生效，而不是只在 normal LB。

## 评价

方向明确但**实现路径有分歧**（stopper 内显式 vs 统一 helper）。Chen Yu 的「统一 helper」被 Prateek 倾向，更利于维护。合入可能性中等，建议作者在 v-next 采纳统一 helper + schedstat 计数后再推进。与 08-05-005 / 08-04-007 同系列延续。
