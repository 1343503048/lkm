# sched debug per cpu debugfs files

# sched/debug: 引入 per-CPU 的 debugfs 文件

## 摘要

本系列为调度子系统引入 **per-CPU 的 debugfs 文件**，把原本只能在全局 `/proc/sched_debug` 或 `debugfs/sched/` 里聚合查看的每 CPU 状态，拆解成 `debugfs/sched/cpuN/` 下的独立文件，便于针对单核观测（如某个 CPU 的 rq 长度、curr、clock、开关 tick 状态等）。

本日要点（Re: v2，22478）：
- 作者发 v2，主要变化：把文件创建从「模块加载时一次性建全局树」改为「按 CPU 热插拔（cpuhp）回调动态增删 `cpuN` 目录」，避免离线 CPU 留下陈旧的 debugfs 节点。
- Peter 的 review 关注两点：
  1. per-CPU 文件的 `show()` 回调必须正确持有对应 `rq` 锁（或 `rcu`），否则读 `rq->curr` / `rq->clock` 可能读到撕裂值；
  2. debugfs 与 `sched_debug` 现有全局输出应保持字段一致，避免两份实现漂移（建议复用 `sched_debug_show()` 的字段抽取函数）。

## 技术细节

新增结构（示意）：
```
/sys/kernel/debug/sched/cpu0/rq_clock
/sys/kernel/debug/sched/cpu0/curr
/sys/kernel/debug/sched/cpu0/nr_running
/sys/kernel/debug/sched/cpu0/nohz
...
```
通过 `cpuhp` 的 `CPUHP_AP_ONLINE_DYN` 阶段注册/注销，离线 CPU 的目录随之移除。

Peter 关注点：
- 读取 `rq->curr` 需要在 `raw_spin_lock_irq(&rq->lock)` 或至少 `rcu_read_lock()` 下，否则在 task 切换瞬间可能读到半更新指针。
- 与全局 `sched_debug` 的字段来源应统一，防止将来一处改了另一处没改。

## 影响与风险

- 影响面：仅 debugfs 观测接口，不影响调度决策；对排查「某特定 CPU 卡住 / 不停 tick / rq 异常」类问题有用。
- 风险：中。并发读取保护若处理不当，可能在 `cat` 时触发 KCSAN / 读到不一致快照；需小心 `rq` 锁持有时长（debugfs 读路径不应长时间持锁阻塞调度）。
- 收益：单核级可观测性，避免为了看一个 CPU 而 dump 全部 CPU 的全局输出。

## 评价

调试可视性增强，方向合理。Peter 已介入 review，主要关卡在「并发读取保护」与「字段与全局输出一致性」。合入可能性中等，建议采纳 Peter 的锁/复用建议后推进。

---
subject: "sched debug per cpu debugfs files"
id: sched-20260805-009
date: "2026-08-05"
title: "sched/debug: 引入 per-CPU 的 debugfs 文件"
series: "Introduce per-CPU debugfs files"
type: feature
status: under_review
severity: medium
merge_likelihood: medium
tags: [sched_debug, topology]
authors: ["Vineeth Pillai <vineeth@vit.edu>", "Peter Zijlstra <peterz@infradead.org>"]
reviewers: ["Peter Zijlstra <peterz@infradead.org>"]
related_articles: []
emails: ["uid-22478@qq-imap"]
---
