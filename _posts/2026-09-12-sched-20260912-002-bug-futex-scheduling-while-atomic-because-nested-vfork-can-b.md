---
id: sched-20260912-002
subject: '[BUG] futex: scheduling-while-atomic because nested vfork can break guard(private_hash)'
date: '2026-09-12'
subsystem: sched
type: bug
status: under_review
severity: medium
thread_root_msgid: <CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com>
lore_url: https://lore.kernel.org/all/20260911175112.uipptpp545u5v5qp@offworld/
authors:
- Peter Zijlstra
maintainers_involved:
- Peter Zijlstra
- Davidlohr Bueso
current_version: 内联修正提案
patch_series:
- version: 内联修正提案
  msgid: <20260911090447.GT788244@noisy.programming.kicks-ass.net>
  date: 2026-09-11
  summary: need_futex_hash_allocate_default() 不再排除 CLONE_VFORK（2 行）；PeterZ 确认治愈测试用例。
  review_outcome: 09-12 Davidlohr Bueso（引入排除的作者）：当初未测量、完全接受该修法并致歉；正式补丁仍未投递。
upstream_commit: null
fixes_commit: ee9dce44362b
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 修正尚未转正为带 Fixes 的正式补丁
  next_action: 把内联 diff 转正为补丁后走 futex 树收取
contribution_opportunities:
- kind: new_patch
  description: 把内联 diff 转正为正式补丁（Fixes/Closes/双方认可说明）
- kind: testing
  description: 高频 vfork+exec 负载量化私有 hash 分配开销
generated_at: '2026-09-14T12:40:00'
source_email_count: 1
related_articles:
- sched-20260911-013
tags:
- regression
title: '[BUG] futex: scheduling-while-atomic because nested vfork can break guard(private_hash)'
layout: article
---

## TL;DR
nested vfork 触发 scheduling-while-atomic 的 futex bug 当日迎来关键收尾：引入问题排除逻辑的 Davidlohr Bueso 亲自回帖——「没真正测过，完全接受 Peter 的 fixlet，抱歉弄坏了东西」，解除了 09-11 遗留的「当初为何排除 vfork」疑问。修复路线（PeterZ 的 2 行改动）获当事双方认可，仅剩正式补丁未投递。本文为增量更新，bug 定性见 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-013-bug-futex-scheduling-while-atomic-because-nested-vfork-can-b.html">sched-20260911-013</a>。

## 背景与问题
need_futex_hash_allocate_default() 排除 CLONE_VFORK（commit ee9dce44362b 引入），nested vfork 场景可打破「单线程进程无私有 futex hash」的前提，在原子上下文触发调度。Peter Zijlstra 09-11 给出治愈测试用例的 2 行修正（不再排除 vfork），当时待确认两点：历史排除原因、性能权衡。

## 技术方案
（承 <a class="article-ref" href="/lkm/2026/09/11/sched-20260911-013-bug-futex-scheduling-while-atomic-because-nested-vfork-can-b.html">sched-20260911-013</a>：`need_futex_hash_allocate_default()` 的条件从 `(clone_flags & (CLONE_VM | CLONE_VFORK)) == CLONE_VM` 改为 `clone_flags & CLONE_VM`。）当日无新代码；新增的是关键证词——Davidlohr Bueso 回应 Jann Horn 的动机分析（该排除只是单线程 vfork+exec 的性能优化）：「Right, but didn't really measure anything and am certainly fine with Peter's fixlet. Sorry for breaking things.」——即当初未做测量、接受 Peter 的修法并致歉。

## 版本演进与当前进展
*current_version: 无版本化补丁（修复仍以 09-11 PeterZ 的线程内联 diff 形态存在，尚未转正为带 Fixes 的正式 PATCH）*。当日线程新增 1 封（Davidlohr Bueso，09-12 01:51 入缓存）。

## Maintainer 意见与讨论焦点
- **Davidlohr Bueso**（ee9dce44362b 作者）：承认当初未测量、接受 Peter 的修正并致歉——修复的最大不确定性（移除排除的动机与代价）就此解除；
- **Peter Zijlstra**（承 09-11）：修正作者，确认治愈测试用例；
- 至此 tglx 转问 bigeasy 的历史问题实际已由原作者作答；当日缓存内未见 Sebastian/tglx 的后续确认。

## 合入评估
*likelihood=high*：修复作者与引入者双方认可，技术路线无分歧；修正体积极小且已验证治愈用例。*blocking_issues*：修正尚未转正为正式补丁（无 Fixes: ee9dce44362b 标签的 PATCH 邮件）；Sebastian/tglx 的最终收取动作未发生（当日缓存内不可见）。*next_action*：PeterZ（或社区）把内联 diff 转正为补丁并附 Fixes/报告者 tag，随后走 futex 树收取。

## 效果评估
效果证据不变：PeterZ 确认 nested vfork 测试用例不再触发 scheduling-while-atomic。Davidlohr 明确「didn't really measure anything」——移除排除给 vfork+exec 增加的私有 hash 分配开销仍无量化数据，但现在被双方接受为可忽略代价（作者主观判断，未见数据）。

## 我可以参与的点
- kind=new_patch：把 PeterZ 的内联 diff 转正为正式补丁（Fixes: ee9dce44362b + Closes 报告链接 + Davidlohr/Peter 的认可说明）——修复共识已齐、只欠正式投递，是当前最直接的贡献点。
- kind=testing：高频 vfork+exec 负载的微基准补一份开销数据（承 09-11 的参与点），让「可忽略」有数字支撑。

## 参考链接
- Davidlohr Bueso 的认可回帖：https://lore.kernel.org/all/20260911175112.uipptpp545u5v5qp@offworld/
- PeterZ 的定位与修正提案：https://lore.kernel.org/all/20260911083639.GX776954@noisy.programming.kicks-ass.net/
- PeterZ 的确认与 diff：https://lore.kernel.org/all/20260911090447.GT788244@noisy.programming.kicks-ass.net/
- 原始报告（09-10）：https://lore.kernel.org/all/CAG48ez26PrUOb8er9TP1gWLsqVLU8TEDr+1Zs25fgH0++=zhUQ@mail.gmail.com/
