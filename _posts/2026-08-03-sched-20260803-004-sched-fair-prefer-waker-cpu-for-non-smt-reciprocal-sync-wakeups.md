---
subject: sched fair prefer waker cpu for non smt reciprocal sync wakeups
id: sched-20260803-004
date: 2026-08-03
subsystem: sched
type: discussion
status: under_review
severity: none
thread_root_msgid: <unknown>
lore_url: unknown
authors:
- Venkatesh Srinivas
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
- Vincent Guittot
current_version: v3
patch_series:
- version: v3
  msgid: <unknown>
  date: 2026-08-03
  summary: 'Re: [PATCH v3] sched/fair: Prefer waker CPU for non-SMT reciprocal sync
    wakeups。Venkatesh Srinivas 在 review 中呼吁先定义 sync wakeup 的整体策略（policy），而非零散修补：是否总选
    waker cpu、是否优先 idle core、何时回退到 waker 的 LLC vs current LLC 等。'
  review_outcome: review 未反对方案本身，但要求先明确 sync vs non-sync wakeup 的策略定义，并举例 Networking
    已存在 sync api 的滥用，提示需统一语义。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 尚未就 sync wakeup 的统一策略达成共识；需要作者/维护者明确 policy 边界（SMT/非SMT、idle core 优先、LLC 回退顺序）
  next_action: 等待对 sync wakeup 整体策略的定义讨论收敛后，再确定该 v3 补丁的定位（是 policy 的一部分还是独立优化）。
contribution_opportunities:
- kind: discussion
  description: sync wakeup 的语义边界（何种负载下选 waker cpu、idle core 优先级、LLC 回退顺序）目前无人给出完整定义，可基于各架构
    SMT 拓扑调研提出 policy 草案参与讨论。
generated_at: '2026-08-04T00:20:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- load_balance
- topology
- hyperthreading
title: sched fair prefer waker cpu for non smt reciprocal sync wakeups
layout: article
---

# sched/fair: 非 SMT reciprocal sync wakeup 优先选 waker CPU（待定义策略）


## TL;DR
`sched/fair` 的「非 SMT  reciprocal sync wakeup 优先选 waker CPU」补丁（v3）引发更深层的讨论：review 要求先定义 sync wakeup 的整体策略，而非零散修补。合入取决于策略共识，目前 medium。

## 背景与问题
sync wakeup（waker 与被唤醒者后续会同步通信）经典做法是把被唤醒任务放在 waker 所在 CPU 以利用热缓存。但当涉及 SMT、idle core、LLC 边界时，行为缺乏统一 policy，导致各处零散修补且 Networking 子系统已出现 sync api 的「滥用」。

## 技术方案
v3 补丁针对非 SMT 场景的 reciprocal sync wakeup 优先选 waker CPU。但 review 指出这只是在更大 policy 缺口上的局部修补。Venkatesh Srinivas 提出的待解决问题清单：

- sync wakeup 是否应在「waker 是唯一运行任务」时选其 CPU？总是如此还是仅特定情况（如 !smt、特定架构）？
- 是否仍优先选 idle core，否则选 waker CPU/Sibling？
- 回退时是选 waker 的 LLC 还是 current 的 LLC，再在其中选 CPU 或最近使用 cpu（prev_cpu）？

## 版本演进与当前进展
当前处于对 v3 的 review 讨论（2026-08-03）。核心转变：从「评审这个补丁」转向「先定义 sync wakeup 策略」。尚无结论。

## Maintainer 意见与讨论焦点
Venkatesh Srinivas（review）明确：应先定义 policy，「if it is not too late for it」。并指出 Networking 已出现 sync api 的 use/abuse，暗示需要统一语义。这是方向性分歧——不是反对，而是认为范围不够。

## 合入评估
合入可能性 medium。阻塞点在于 sync wakeup 统一策略未定义。需先在邮件列表就 policy 边界达成共识。

## 效果评估
邮件未提供 benchmark 数字，属调度策略讨论，无量化效果数据。

## 我可以参与的点
- 这是明确的讨论参与点：可基于 x86/arm64 等不同 SMT 拓扑调研，提出 sync wakeup 的统一 policy 草案（覆盖 SMT/非SMT、idle core 优先、LLC 回退顺序），回帖到该 thread。

## 参考链接
- lore thread: 未获取到
