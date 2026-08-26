---
title: "sched/debug：引入 per-CPU debugfs 文件（v6，rq->rd 加 __rcu 注解）"
date: 2026-08-26
tags: [sched/core, documentation]
series: "sched debug per-cpu debugfs files"
type: fix
severity: low
status: under_review
related_articles: ["sched-20260825-010-sched-debug-percpu-debugfs-v5.md"]
lore: ""
---

## 概述

（本文为增量更新，完整背景见 related_articles 中 08-25 的 v5 文章）

`sched/debug` 系列推进到 **v6**（UID 57937 00/6 封面 + 57938..57942，含 Re: 57736、58137）。核心动机不变：`struct rq` 的 `rd`（root_domain）指针经 RCU 动态更新、经 `rq_attach_root()` 的 `call_rcu()` 延迟回收，但 `rq->rd` 字段缺 `__rcu` 注解，且调度子系统内多处无锁读者直接访问 `rq->rd` 而未用 RCU 解引用原语。

v6 的 1/6（据 57937 正文）即为「Annotate rq->rd with __rcu and update lockless readers」：在 `kernel/sched/sched.h` 给 `rq->rd` 加 `__rcu`，并把 `kernel/sched/` 下各处无锁读者改为 `rcu_dereference()` / `rcu_dereference_sched()` / `rcu_access_pointer()`（core.c +16/-6、deadline.c +8/-4、fair.c +29/-15、sched.h +2/-1）。

## 改动内容 / 核心补丁

- 1/6 `sched: Annotate rq->rd with __rcu and update lockless readers`
- 2/6 `sched/debug: Protect lockless rq->rd access in print_dl_rq()`
- 3/6 `sched/debug: Protect lockless rq->curr access in print_cpu()`
- 4/6 `sched/debug: Protect p->mm access in sched_show_numa()`
- 5/6 `sched/fair: Use list_for_each_entry_rcu() in print_cfs_stats()`
- 6/6 `sched/debug: Introduce per-CPU debugfs files`

## 状态与讨论

- 当前状态：**under_review**（v6，已迭代多轮）。
- 收益：保证各架构数据依赖屏障、启用 Sparse 校验、明确 RCU 读侧所有权契约。合入概率高。
- 与 08-25 v5 相比为常规修订（具体 changelog 以 cover 为准）。

## 关联

- 08-25 010 sched/debug per-CPU debugfs v5
