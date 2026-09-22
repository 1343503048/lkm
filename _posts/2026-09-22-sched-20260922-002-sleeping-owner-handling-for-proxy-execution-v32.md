---
id: sched-20260922-002
date: '2026-09-22'
subject: Sleeping Owner Handling for Proxy Execution (v32)
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260922024117.1514332-1-jstultz@google.com>
lore_url: https://lore.kernel.org/all/20260922024117.1514332-1-jstultz@google.com/
authors:
- John Stultz
- K Prateek Nayak
maintainers_involved:
- Peter Zijlstra
current_version: v32
patch_series:
- version: v31
  msgid: null
  date: '2026-09-02'
  summary: 上一迭代，见 sched-20260902-001
  review_outcome: Peter 接手大部分简单补丁，余 sleeping owner 处理
- version: v32
  msgid: <20260922024117.1514332-1-jstultz@google.com>
  date: '2026-09-22'
  summary: rebase 到 tip/sched/core；加入 K Prateek 的 activate-blocked-donor；采纳 Atul 复检
    is_blocked；guard() 风格整理；修复 proxy_remove_from_sleeping_owner 竞态
  review_outcome: 待 Peter 在两方案间表态
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
  - Peter 尚未在 John 与 K Prateek 两套方案间表态
  - 逻辑复杂度高，locking 部分需要更多 review
  next_action: Peter 表态后作者按选择打磨并吸收反馈
contribution_opportunities:
- kind: review
  description: 作者公开征求简化的 review 意见，尤其 locking 与树状唤醒级联
- kind: testing
  description: 启用 proxy execution 的构建上压测 mutex 阻塞/唤醒场景
- kind: discussion
  description: 对比 John 与 K Prateek 两套实现，为 Peter 取舍提供分析
generated_at: '2026-09-23T00:00:00'
source_email_count: 3
related_articles:
- sched-20260902-001
tags:
- proxy_execution
- core_sched
title: Sleeping Owner Handling for Proxy Execution (v32)
layout: article
---

## TL;DR
John Stultz 发出 proxy execution 旅程第 5 阶段「Sleeping Owner Handling」的第 32 版迭代（2 补丁）：当任务阻塞在一个 owner 正在睡眠的 mutex 上时，把 waiter 停用（deactivate）并挂到 owner 的等待表上，待 owner 唤醒时在同一 runqueue 上重新激活，使其得以提升 owner。v32 新增 K Prateek 的「无 owner 时激活 blocked donor」补丁，并整合 Atul Kumar Pant、Peter 的风格与竞态修复意见。仍在征求 Peter 在他与 K Prateek 两套方案之间取舍，属 RFC 待评审。

## 背景与问题
Proxy execution 提交路径分步推进：1) prep、2) 单 rq 代理、3) 简单 donor 迁移、4) 优化 donor 迁移、5) sleeping owner 处理（当前阶段）、后续还有 chain 平衡、proxy rwsem 等。任务阻塞在 mutex 上时，若 owner 本身在睡眠，此时没有任何手段能提升睡眠中的 owner，必须在 owner 唤醒时重新激活 waiter 以提升其运行。

## 技术方案
停用 waiter 并将其排入 owner 的任务表，owner 唤醒时激活这些 waiter 到同一 runqueue，使 waiter 得以 boost owner 运行。难点在于：waiters 可形成树状结构，树中间的任务也可能被唤醒，唤醒沿树级联而下需额外列表来规避递归。

v32 新增 K Prateek 的 `sched/core: Activate blocked donor when no owner is found`：mutex 慢路径中若未观察到 owner 就唤醒 blocked donor 让其抢锁，避免 donor 被停用后要等它成为 first waiter 才被自然唤醒而中断代理。

## 版本演进与当前进展
v32 相对上一版：rebase 到当前 `-tip/sched/core`；加入 K Prateek 的「无 owner 时激活 blocked donor」；采纳 Atul Kumar Pant 建议在 `do_activate_blocked_waiter()` 中复检 `is_blocked`；按 Peter 意见采用 `guard()` 做大量风格/格式整理；修复 `proxy_remove_from_sleeping_ow...` 中的潜在竞态。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra** 已在前几轮接手了大部分简单补丁，剩下的主要是 sleeping owner 处理。John 在 cover 中请 Peter 在他与 K Prateek 方案之间表态：「Hopefully you can provide some input as to which approach you'd prefer?」
- **K Prateek Nayak** 此前独立发过自己的同主题方案（<https://lore.kernel.org/lkml/20260826062901.2137-1-kprateek.nayak@amd.com/>），John 认为其方案有明确好处但还需打磨、也更难理解，故选择继续迭代自己的方案，并吸收了他的一处通用修复。
- 争议核心：两套 sleeping-owner 处理的实现路径取舍尚未由维护者定夺。

## 合入评估
likelihood=unknown。proxy execution 整体仍处 RFC 阶段（前置阶段补丁正被 Peter 陆续收取），本阶段补丁等待 Peter 对方案取舍的表态。blocking_issues：两套方案未定、逻辑复杂度高且作者自述 locking 部分尤其别扭、需更多 review。next_action：Peter 在两方案间表态，随后作者按选择打磨并吸收反馈。

## 效果评估
无性能数据，仅为 proxy execution 正确性功能补丁；作者自述该逻辑「简单的东西藏着微妙」，正确性风险集中在唤醒级联与竞态。

## 我可以参与的点
- **review**：作者明确表示「I'd very much appreciate review and feedback for ways to simplify this」，尤其欢迎指出 confusing 处与可简化方向（locking/树状 waiter 唤醒级联）。
- **testing**：在启用 proxy execution 的构建上跑 mutex 阻塞/唤醒压力场景，验证 sleeping owner 路径与竞态。
- **discussion**：对比 John 与 K Prateek 两套方案，为 Peter 的取舍提供分析。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260922024117.1514332-1-jstultz@google.com/
- K Prateek 同主题方案: https://lore.kernel.org/lkml/20260826062901.2137-1-kprateek.nayak@amd.com/
