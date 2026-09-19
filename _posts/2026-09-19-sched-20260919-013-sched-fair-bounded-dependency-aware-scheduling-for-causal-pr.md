---
id: sched-20260919-013
date: '2026-09-19'
subject: 'sched/fair: bounded Dependency-Aware Scheduling for causal progress'
subsystem: sched
type: discussion
status: rfc
severity: none
thread_root_msgid: <CADNJy8DbyKti51DesJd8bCX0evNPpJkav+TNEuyh_rQce=oGHQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/CADNJy8DbyKti51DesJd8bCX0evNPpJkav+TNEuyh_rQce=oGHQ@mail.gmail.com/
authors:
- Julian Blaauwiekel
maintainers_involved: []
current_version: v1
patch_series:
- version: RFC
  msgid: <CADNJy8DbyKti51DesJd8bCX0evNPpJkav+TNEuyh_rQce=oGHQ@mail.gmail.com>
  date: '2026-09-19'
  summary: DAS 设计讨论：有界依赖压力调整服务顺序但不创造配额
  review_outcome: 刚发出，暂无回复
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - 无社区反馈，方案与现有调度机制边界未评估
  next_action: 等待社区判断是否已有等价机制、方案是否值得继续
contribution_opportunities:
- kind: discussion
  description: 指出 DAS 与 proxy execution/priority inheritance/EEVDF 的重叠与增量价值
- kind: review
  description: 评估 ordering 而非 entitlement 不变式在 EEVDF 下的可行性与公平性风险
generated_at: '2026-09-20T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- eevdf
title: 'sched/fair: bounded Dependency-Aware Scheduling for causal progress'
layout: article
---

## TL;DR
新 RFC（设计讨论，未附补丁）：16 岁的 Julian Blaauwiekel 在其自研 OS MUDOS_64 的调度器 HEDFS-4 中提出"Dependency-Aware Scheduling (DAS)"——当一个已 runnable 的任务 B 成为另一任务 A 因果关键路径上的一环时（A 等 B，但 B 本已 runnable，故无 wakeup 事件传递该信息），给 B 施加有界、可消耗的"依赖压力"以调整短期服务顺序，但明确不创造 CPU 配额。作者发 RFC 寻求社区指出是否已有等价机制。本日无回复。

## 背景与问题
作者以 Linux 7.2.6 fair 调度器为对标设计 HEDFS-4，想在不明显牺牲吞吐/公平的前提下超越之，从而归纳出 DAS。核心观察：一个 runnable 任务可以在不发生 runnable 状态迁移的情况下，变得对系统进度重要——`A 提交工作给 B 然后阻塞等 B 完成`，B 从 runnable 到 runnable，没有新的 wakeup 通知"B 刚进入 A 的关键路径"。EEVDF 对 B 的公平服务状态仍然正确，但依赖是正交于 B 的 lag/virtual deadline 的信息。作者发 RFC 是因可能忽略了已有机制或先前研究。

## 技术方案
- 核心不变式：**依赖信息只能改变短期服务顺序，绝不能创造 CPU 配额**——不改任务 weight、不抹 vruntime 债、不给未记账运行、不永久提优先级、不跨调度类。B 因依赖被提前的每一份 delta_t 仍正常记到 B 头上。
- 依赖来源：waiter→mutex owner、client→IPC/server、consumer→producer、requester→completion worker 等，比传统优先级继承（主要处理资源所有权的优先级反转）更宽，即使 A/B 同优先级、B 不持传统锁、B 已 runnable 也成立。
- 有界压力：初始依赖压力约 0.5ms 服务当量、总压力上限约 8ms、排序偏置约 1ms 虚服务当量（作者强调是调优值非常量）；压力随实际进度消耗，依赖完成/失效/不可进展即移除或挂起；长链按 `depth_factor(d)=1/2^(d-1)` 衰减，fan-in 亦次线性。
- 不在 schedule() 里做图遍历：惰性决策架构，仅维护有界 actionable frontier（如 k≤64，维护 O(log k)）；fast path O(1)（Winner_Certificate 校验 `Can_Current_Continue()`），直接因果交接（DIRECT_HANDOFF）只在必要时才做真实 LOCAL_REPICK 或 PLACEMENT。
- 切换盈利性门控：逻辑偏好 vs 物理切换成本（调度开销、TLB/cache、地址空间等），避免每个小变化都触发上下文切换。

作者澄清：80% 改善等来自 HEDFS-4/MUDOS 上下文，**不**构成对 Linux 的证明；最希望看到的是 Linux 原生实现 + 受控 ablation。文末说明"本文经 AI 辅助撰写，调度器设计与技术主张为作者本人"。

## 版本演进与当前进展
v1/RFC 刚发出（本日 23:36），暂无 review 意见。

## Maintainer 意见与讨论焦点
本日无维护者/社区回复。可预见的讨论焦点：DAS 与现有机制的边界——proxy execution（阻塞的 donor 迁移）、优先级继承、EEVDF 的 lag/虚拟截止期，以及"ordering 而非 entitlement"不变式在 EEVDF 框架下是否自洽、是否会破坏公平性保证。

## 合入评估
likelihood=unknown。纯设计 RFC、未附补丁、无任何社区反馈，证据不足以判断合入可能性。blocking_issues：无社区反馈；方案与现有调度机制的边界未评估。next_action：等待社区（尤其 sched/fair 维护者）判断是否已有等价机制、方案是否值得继续。

## 效果评估
作者引用的"80% 改善"等为其 HEDFS-4/MUDOS 上下文数据，作者明确说明不代表对 Linux 成立、需 Linux 原生实现 + 受控 ablation 才能判定——属"作者主观判断，未见 Linux 测试数据"。无 Linux 性能数据。

## 我可以参与的点
- kind=discussion：指出 Linux 已有的同类机制（proxy execution、priority inheritance、EEVDF lag 处理、sync wakeup）与 DAS 的重叠/差异，帮助作者厘清增量价值。
- kind=review：评估"ordering 而非 entitlement"不变式在 EEVDF 公平性框架下的可行性，以及有界依赖压力是否会引入饥饿/优先级反转。

## 参考链接
- lore（RFC）: https://lore.kernel.org/all/CADNJy8DbyKti51DesJd8bCX0evNPpJkav+TNEuyh_rQce=oGHQ@mail.gmail.com/
