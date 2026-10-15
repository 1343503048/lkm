---
id: sched-20261015-005
date: 2026-10-15
subject: 'sched/idle: Make forced polling state race-safe'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261015094211.4156055-1-sh_def@163.com>
lore_url: https://lore.kernel.org/all/20261015094211.4156055-1-sh_def@163.com/
authors:
- Hui Su
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261015094211.4156055-1-sh_def@163.com>
  date: 2026-10-15
  summary: cpu_idle_force_poll 改 atomic_t，并把 fallback 永久状态与临时请求计数分开
  review_outcome: 暂无 review
upstream_commit: null
fixes_commit: d16699123434
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 暂无 review
  next_action: 等 idle/sched 维护者 review；在真正使用弱 fallback 的架构上补测
contribution_opportunities:
- kind: review
  description: 审视 fallback 永久状态与临时计数拆分在弱 arch_cpu_idle() 架构上的语义
- kind: testing
  description: 在使用弱 arch_cpu_idle() fallback 的架构上验证 polling 不被误关
generated_at: '2026-10-16T01:05:00'
source_email_count: 1
related_articles: []
tags:
- idle
title: 'sched/idle: Make forced polling state race-safe'
layout: article
---

## TL;DR
Hui Su 修复 `cpu_idle_poll_ctrl()` 的强制 idle polling 嵌套计数竞态：该全局计数用普通自增/自减维护，而各 idle CPU 无同步地读它，KCSAN 报出 data race。补丁改用 `atomic_t` 计数，并把弱 `arch_cpu_idle()` fallback 永久切换 polling 的状态与「临时请求计数」分开保存，避免并发请求覆盖或误释放 fallback 状态。带 `Fixes: d16699123434 ("idle: Implement generic idle function")`，当日无 review。

## 背景与问题
`cpu_idle_poll_ctrl()` 维护一个全局嵌套计数表示「强制 idle polling」的请求数。计数用普通 `++/--` 更新，而 idle CPU 在决定是否 poll 时读取它，两者无同步——KCSAN 两 worker harness 复现了该 data race（修改前计数跑到 −14565）。此外，弱 `arch_cpu_idle()` fallback（`cpu_idle_force_poll`）会永久把通用 idle 路径切到 polling；若它与临时请求计数混用同一变量，并发请求可能覆盖、或在临时计数归零时误把 fallback 状态也释放掉。

## 技术方案
单补丁（kernel/sched/idle.c，+15/−9）：
- `static int __read_mostly cpu_idle_force_poll` 改为 `static atomic_t __read_mostly cpu_idle_force_poll = ATOMIC_INIT(0)`。
- 计数改用原子增减，使 idle 侧的读取 race-free。
- 把「fallback 永久 polling 状态」与「临时请求计数」拆成两个独立状态，避免并发请求覆盖或后续释放 fallback。

作者测试：x86_64 两 worker KCSAN harness 修改前以 −14565 结束，10 万次平衡请求后归零且无 target 报告；KCSAN/noinstr 构建无 objtool 警告；聚焦测试确认临时计数归零后 polling 仍保持（x86 上弱 fallback 本身未被实际执行）。

## 版本演进与当前进展
v1 刚发出（<20261015094211.4156055-1-sh_def@163.com>），暂无 review 意见。

## Maintainer 意见与讨论焦点
暂无维护者表态。潜在关注点：弱 `arch_cpu_idle()` fallback 与临时请求状态的语义拆分是否在非 x86 架构（真正使用该 fallback 的架构）上行为一致，需相关维护者确认。

## 合入评估
*likelihood=unknown*。改动小而自洽，但当日无任何 review。*blocking_issues*：无 review。*next_action*：等 idle/sched 维护者 review；可在真正使用弱 fallback 的架构上补测。

## 效果评估
KCSAN data race 消除（作者自测：10 万次平衡请求计数归零、无 target 报告）。无性能数据，属正确性/竞态修复。

## 我可以参与的点
- *review*：审视「fallback 永久状态」与「临时计数」拆分后，弱 `arch_cpu_idle()` 架构上的语义是否保持。
- *testing*：在真正使用弱 `arch_cpu_idle()` fallback 的架构上验证 polling 不会因临时计数归零而被误关。

## 参考链接
- patch：https://lore.kernel.org/all/20261015094211.4156055-1-sh_def@163.com/
