---
id: sched-20260817-005
date: 2026-08-17
subsystem: sched
type: feature
status: under_review
severity: medium
thread_root_msgid: <uid-43009@qq-imap>
lore_url: 未获取到
authors:
- Shrikanth Hegde
- K Prateek Nayak
maintainers_involved:
- Peter Zijlstra
- K Prateek Nayak
- Joel Fernandes
current_version: v10
patch_series:
- version: v10
  msgid: <uid-43009@qq-imap>
  date: 2026-08-17
  summary: steal_governor v10 讨论回复：回应 32 位 ARM64 的 BUG()、迁移禁用下的抢占风暴、以及 task_rq_lock()
    在 SRCU 读区内的 irq 死锁风险，给出修复方向与基准。
  review_outcome: 讨论中，Prateek/K Prateek 给出多项修复建议；Shrikanth 已基本采纳并给出新基准（steal 命中 +58%、特定负载提速）。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - irq 死锁修复需重新设计锁序、32 位 BUG 需 arch 条件编译、抢占风暴需细粒度额定
  next_action: 等待 Shrikanth 出 v11 落实各项修复。
contribution_opportunities:
- kind: testing
  description: 在 32 位 ARM64 + 高 NUMA 节点机器上验证 steal 路径无 BUG/死锁；运行 hackbench/kernbench
    看 steal 命中提升是否转化真实提速。
generated_at: '2026-08-18T00:10:00'
source_email_count: 2
related_articles: []
tags:
- sched/fair
- numa
- idle
title: 'sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff'
layout: article
---

## TL;DR
`steal_governor` v10 的讨论回复（Shrikanth Hegde，接 Prateek/K Prateek/J Joel 等 review）：系列引入"preferred CPUs"与"steal-driven vCPU backoff"，让空闲/轻载 CPU 从忙 CPU 偷取任务以减少空闲时间。本日回复集中回应三处缺陷——① 32 位 ARM64 上 `atomic_long` 位运算触发 `BUG()`；② 迁移禁用（migration disabled）任务在 steal 下造成"抢占风暴"；③ `task_rq_lock()` 在 SRCU 读区内持有会触发 IRQ 死锁。Shrikanth 基本采纳并给出新基准（steal 命中 +58%、kernbench/hackbench 提速）。仍在 v10 讨论，待 v11 落实修复。

## 背景与问题
`steal_governor` 通过让轻载/空闲 CPU 主动从忙 CPU "偷"任务来降低整机空闲率。但早期实现有结构性缺陷：
1. **32 位 ARM64 BUG**：用 `atomic_long` 位运算处理 CPU 掩码，在 32 位架构上超过字长触发 `BUG()`。
2. **抢占风暴**：被偷任务若处于 `migration_disabled` 态，反复尝试迁移造成高频率抢占/重调度风暴。
3. **IRQ 死锁**：`task_rq_lock()` 在 SRCU 读区内持 rq 锁，而 SRCU 读区可被 IRQ 重入，形成 rq 锁 ↔ SRCU 的潜在死锁。

## 技术方案（讨论中的修复方向）
- 32 位 BUG：位掩码改用 per-arch 适配（如 `cpumask` 位操作或 `unsigned long` 数组），避免 `atomic_long` 超长位运算。
- 抢占风暴：对 `migration_disabled` 任务不执行 steal，或加 backoff 节流。
- IRQ 死锁：把 `task_rq_lock()` 移出 SRCU 读区，或改用 `task_rq_lock_irqsave()` 重排锁序，确保 rq 锁不在 SRCU 读区内持有。
Shrikanth 在回复中给出修复后基准：steal 命中从某基线 +58%，kernbench（12 线程）与 hackbench（8 笔/进程）均提速。

## 版本演进与当前进展
- v10（12 patch）属于 `steal-governor` 长系列，本日（08-17）Shrikanth 回复 43009 为对多位 reviewer 的集中回应。
- Prateek Nayak 等此前提出上述缺陷；Shrikanth 基本采纳，承诺 v11 落实。

## Maintainer 意见与讨论焦点
- K Prateek Nayak / Prateek / Joel Fernandes：指出 32 位 BUG、抢占风暴、IRQ 死锁三处问题。
- Shrikanth Hegde：确认问题并给出修复方向与基准，倾向 v11 修复。

## 合入评估
合入可能性中等。方向（idle-steal 降低整机空闲）受关注，但三处结构性缺陷需 v11 修复后才能进入 tip。阻塞点：IRQ 死锁需重新设计锁序（较敏感），32 位需条件编译。

## 效果评估
修复后基准：steal 命中 +58%；kernbench/hackbench 提速（具体百分比邮件未详列，但称"明显"）。需更多现实负载验证。

## 我可以参与的点
- 在 32 位 ARM64 + 高 NUMA 节点机器验证 steal 无 BUG/死锁；跑 hackbench/kernbench 看命中提升是否转化真实提速。

## 参考链接
- lore thread: 未获取到
- tip-bot commit: 未获取到
- stable backport: 未获取到
