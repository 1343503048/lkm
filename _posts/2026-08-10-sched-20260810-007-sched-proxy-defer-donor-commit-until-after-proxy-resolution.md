---
id: sched-20260810-007
date: 2026-08-10
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260810093631.xxxxxx-xukai@kernel.org>
lore_url: 未获取到
authors:
- Xukai Wang
maintainers_involved:
- Peter Zijlstra
- Juri Lelli
- Joel Fernandes
- Valentin Schneider
current_version: RFC v2
patch_series:
- version: RFC v2
  msgid: <20260810093631.xxxxxx-xukai@kernel.org>
  date: 2026-08-10
  summary: RFC v2：将 donor（代理执行）任务的 commit（正式成为 rq->curr）推迟到 proxy 解析完成之后，避免中途状态暴露给负载均衡/调度统计。
  review_outcome: RFC 阶段，等待 proxy execution 维护者对延迟 commit 语义的评审。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - proxy execution 主线尚未完全稳定，延迟 commit 需与核心 proxy 流程对齐
  next_action: 等待 Peter/Juri 对延迟 commit 与现有 proxy 流程冲突的评审。
contribution_opportunities:
- kind: review
  description: 评审 donor commit 推迟对负载均衡/统计/追踪的一致性问题。
- kind: discussion
  description: 参与 donor 任务中途状态可见性边界的讨论。
generated_at: '2026-08-11T00:15:00'
source_email_count: 1
related_articles:
- sched-20260810-001
tags:
- proxy_execution
- sched/core
title: 'sched/proxy: Defer donor commit until after proxy resolution'
layout: article
---

## TL;DR
Xukai Wang 提交 RFC v2「sched/proxy: Defer donor commit until after proxy resolution」。把 donor 任务的 commit（成为 rq->curr）推迟到 proxy 解析完成后，避免中途状态被负载均衡/统计看到。RFC 阶段，合入可能性低（依赖 proxy 主线）。

## 背景与问题
proxy execution 中，donor 任务被临时选为实际运行任务，但此时 proxy 解析（找到持锁 owner 并接管）可能尚未完成。若在解析完成前就把 donor commit 为 `rq->curr`，负载均衡、调度统计、追踪等会看到不一致的中间状态，且若 proxy 解析失败需回滚，复杂度更高。

## 技术方案
将 donor 的 commit 延迟到 proxy 解析成功之后：先完成 owner 选择/接管，再统一把 donor 置为 rq->curr。设计取舍：增加 proxy 路径的阶段性，换取状态一致性，但对 proxy 临界区的长度与唤醒路径有额外约束。

## 版本演进与当前进展
当前 RFC v2。8/10 发出，尚无最终 ack。与同日 001（proxy+scx v11）同属 proxy execution 主题但独立系列。

## Maintainer 意见与讨论焦点
焦点：延迟 commit 与现有 proxy 流程（特别是唤醒/抢占路径）的对齐，以及与 SCX donor 抽象的协调。

## 合入评估
合入可能性 low。proxy execution 主线仍在演进，RFC 需先解决与核心流程的冲突。

## 效果评估
无 benchmark；目标是状态一致性，非性能。

## 我可以参与的点
- 梳理延迟 commit 对唤醒延迟的影响；
- 评审与 001（scx donor 抽象）的接口协调。

## 参考链接
- lore: 未获取到
- 关联: sched-20260810-001（proxy+scx v11）
