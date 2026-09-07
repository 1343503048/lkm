---
id: sched-20260902-003
date: '2026-09-02'
subject: 'sched/cache: Fix use after free mm access in account_mm_sched()'
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: null
lore_url: null
upstream_commit: null
fixes_commit: null
merged_branch: null
current_version: null
generated_at: null
authors:
- Tim Chen
maintainers_involved: []
patch_series: []
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 当天无维护者 review / ack / Reviewed-by
  - task_struct 新增指针的代价未评估
  - '与 proxy execution 下 execution context 归属（sched/cache: Use execution context for
    cache task tick）需一并收敛'
  next_action: 用 KASAN 复现并回测试结论，同时 review 2/2 的 task_struct 尺寸影响
contribution_opportunities:
- 开 CONFIG_SCHED_CACHE + KASAN，用 fork/exec 密集负载复现并验证 0/2
- 量化 task_struct->sched_cache_grp 的尺寸/热路径开销，线程内目前无此数据
- 跟进 deadline donor 场景下 account_mm_sched() 的记账归属
source_email_count: 1
related_articles: []
tags:
- sched/cache
- crash
title: 'sched/cache: Fix use after free mm access in account_mm_sched()'
layout: article
---

## TL;DR

sched/cache 的一个 KASAN use-after-free：`account_mm_sched()` 经 mm 取缓存统计，exec 换掉 mm 后旧 mm
已释放。Tim Chen 9/2 08:08 直接发 0/2 系列，方向是把 sched_cache_group 与 mm 解耦、在 `task_struct`
上直接挂 `sched_cache_grp`。属于高优先内存安全 bug，但当天没有任何维护者评审。

## 背景与问题

`sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务
被 `exec` 替换掉 `mm` 后，旧 `mm` 可能已被释放，若仍持有引用访问即触发
use-after-free（UAF）。相关讨论（Re: UID 72357）已指出该问题。

## 技术方案

系列 `sched/cache: Fix use after free mm access in account_mm_sched()`（UID 72573 0/2
封面）：
- 1/2 `sched/cache: Decouple sched_cache_group from mm`（72574）：把调度缓存组与 `mm`
  解耦，不再依赖可能被替换的 `mm`。
- 2/2 `sched/cache: Introduce task_struct->sched_cache_grp`（72578）：在 `task_struct`
  上直接引入 `sched_cache_grp` 字段，避免使用已释放的 `mm` 派生信息。

## 版本演进与当前进展

- 当前状态：**under_review**（新系列，0/2 封面 + 2 个实现补丁）。
- 严重度：**high**（UAF 属内存安全类 bug，可能导致崩溃/数据损坏）。
- 合入可能性 medium；属调度缓存（LLC 亲和）方向，与 09 系列 sched/cache 工作相关。

## Maintainer 意见与讨论焦点

- 报告者不是内核开发者：cover 明确写 "Hyunwoo Kim reported a KASAN use-after-free in account_mm_sched()"
  （72572）。此前 Hyunwoo Kim 自己发过 `[PATCH] sched/cache: Fix use-after-free of the mm replaced by exec`，
  Tim Chen 在 72363 回帖后，用这个 0/2 系列把它取代——讨论闭环只在「作者 + 报告者」之间。
- Ingo Molnar / Peter Zijlstra 当天未介入该线程，无 ack、无 NAK、无 Reviewed-by。
- 同方向的语义争议在 9/3 继续：Hui Su 发 `sched/cache: Use execution context for cache task tick`（74668），
  Tim Chen 认可但补了一句 "However, the donor may be a deadline…"（75219/75742，截断）。

## 合入评估

**中**。UAF 本身优先级高、补丁体量小（2 个），但没有维护者表态是硬卡点；还需要 (1) 确认在
`task_struct` 上新增指针的代价可接受，(2) 与 proxy execution 的 execution-context 问题（74668）一起收敛，
否则 `account_mm_sched()` 要改两次。

## 效果评估

效果证据只有一份外部 KASAN 报告（Hyunwoo Kim 提出），线程内无任何性能数据。72574 里
"This decouples the scheduler's hot-path…" 属作者判断，未见测试数据。

## 我可以参与的点

- 开 `CONFIG_SCHED_CACHE` + KASAN，用 exec 密集负载（fork+exec 循环）复现该 UAF，确认 0/2 能消掉报告。
- 量化 `task_struct->sched_cache_grp` 带来的结构体尺寸与 cache line 影响——目前没人给过这个数字。
- 跟进 74668 的 deadline donor 问题，它和本系列改的是同一个函数。

## 参考链接

- 009 RFC v2 NUMA 细粒度均衡 + sched/cache 迁移辅助（同属 sched/cache 方向）
