---
title: "sched/debug：引入 per-CPU debugfs 文件（v5，rq->rd 加 __rcu 注解）"
date: 2026-08-25
tags: [sched/core, documentation]
series: "sched debug per-cpu debugfs files"
type: fix
severity: low
status: under_review
lore: ""
---

## 概述

`sched/debug` 系列（v5，UID 57583 00/6 等共 6 个补丁：57503/57505/57506/57531/57543/
57582）引入 per-CPU debugfs 文件，改进调度器调试信息按 CPU 粒度导出。

核心动机（据封面正文）：`struct rq` 的 `rd`（root_domain 指针）通过 RCU 动态更新，
其释放经 `rq_attach_root()` 中的 `call_rcu()` 延迟回收，但 `rq->rd` 字段缺少 `__rcu`
编译器注解，且调度子系统内多处无锁读者直接访问 `rq->rd` 而未使用 RCU 解引用原语。

## 改动内容 / 核心补丁

- 在 `kernel/sched/sched.h` 中为 `rq->rd` 加 `__rcu` 注解。
- 更新 `kernel/sched/` 下各处无锁读者，使其恰当使用 `rcu_dereference()` /
  `rcu_dereference_sched()` / `rcu_access_pointer()`（涉及 core.c、deadline.c、
  fair.c、sched.h，约 30 处增/25 处删）。
- 同步为 `rq->sd` 等使用 `RCU_INIT_POINTER`，并引入 per-CPU debugfs 文件导出相关
  统计（`print_dl_rq` / `print_cpu` / `sched_show_numa` / `print_cfs_stats` 的锁less
  访问加保护）。

## 状态与讨论

- 当前状态：**under_review**（v5，已迭代多轮）。
- 收益：保证各架构上的数据依赖屏障、启用 Sparse 静态分析校验、明确 RCU 读侧所有权
  契约。属健壮性/可维护性改进，合入概率高。

## 关联

- 007 sched：nr_pinned per-CPU 计数器（同为调度核心清理）
- 008 sched：steal_governor（含 sched/debug 迁移统计）
