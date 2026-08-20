---
id: sched-20260810-001
date: 2026-08-10
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260810080120.1512807-1-...@righi.dev>
lore_url: https://lore.kernel.org/lkml/20260810080120.1512807-1-...@righi.dev/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- Tejun Heo
- Ingo Molnar
- Joel Fernandes
- Juri Lelli
current_version: v11
patch_series:
- version: v11
  msgid: <20260810080120.1512807-1-...@righi.dev>
  date: 2026-08-10
  summary: 15 个 patch：为 sched_ext 提供 donor/owner 任务选择抽象（scx_select_cpu_donor()/scx_pick_idle_cpu_donor()
    等新接口），使 BPF 调度器能感知 proxy execution 的 donor 任务，避免 donor 被错误迁移/放置。
  review_outcome: v11 仍 under_review，等待维护者对在 sched_ext 路径暴露 donor/owner 抽象的最终认可。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - sched_ext 路径暴露 donor/owner 抽象需 Peter/Tejun 确认接口稳定性
  next_action: 等待 Tejun/Peter 对 SCX 侧 donor 选择接口的评审意见。
contribution_opportunities:
- kind: review
  description: 评审 scx_select_cpu_donor 等新增接口在不开启 proxy execution 时的开销与正确性。
- kind: testing
  description: 在开启 SCHED_CLASS_EXT 与 CONFIG_PROXY_EXECUTION 的内核上跑 scx 调度器验证 donor
    不被误迁移。
generated_at: '2026-08-11T00:15:00'
source_email_count: 15
related_articles: []
tags:
- sched_ext
- proxy_execution
- sched/core
title: 'sched: Make proxy execution compatible with sched_ext'
layout: article
---

## TL;DR
Andrea Righi 提交 v11「Make proxy execution compatible with sched_ext」——15 个 patch，为 BPF 调度器引入 donor/owner 任务选择抽象，使其能正确参与 proxy execution。目前 under_review。

## 背景与问题
proxy execution 允许被互斥锁阻塞的任务（owner）把 CPU 临时「借」给正在持锁的 donor 任务运行。但 sched_ext（BPF 调度器）在做 CPU 选择/空闲选择时，看不到 donor/owner 这一层关系，可能把 donor 错放到错误的 CPU 或错误地抢占，破坏 proxy 语义。

## 技术方案
系列在 sched_ext 路径新增 donor/owner 感知接口：`scx_select_cpu_donor()`、`scx_pick_idle_cpu_donor()` 等，让 BPF 调度器在选核时基于 donor 任务而非被阻塞的 owner。v11 用 cleanup.h 的 guard 简化锁作用域、把 sched_ext 分片操作改为直接调用新接口、并调整 owner 可用性断言（`task_is_running()` → owner 是否实际在 CPU 上）。设计取舍：仅在 proxy execution 启用时才暴露 donor 语义，普通调度路径无额外开销。

## 版本演进与当前进展
当前 v11（15 patches）。此前提及的 v10 已被 Tejun 的 cleanup 建议推动重构。v11 于 8/10 发出，暂无最终 ack。

## Maintainer 意见与讨论焦点
讨论焦点：sched_ext 侧 donor 选择接口的稳定性，以及 proxy execution 与 SCX 耦合的复杂度。Peter 此前要求更清晰的抽象边界。

## 合入评估
合入可能性 medium。方向被接受，但需 Tejun/Peter 对接口的最终认可；可能与 proxy execution 主线进度挂钩。

## 效果评估
邮件未给 benchmark；属使 SCX 支持 proxy 的基础设施补丁。

## 我可以参与的点
- 评审 donor 选择接口在 non-proxy 路径零开销的保证；
- 在 SCHED_CLASS_EXT + CONFIG_PROXY_EXECUTION 内核上实测 donor 不被错误迁移。

## 参考链接
- lore: https://lore.kernel.org/lkml/20260810080120.1512807-1-...@righi.dev/
- tip 分支: 未合并
