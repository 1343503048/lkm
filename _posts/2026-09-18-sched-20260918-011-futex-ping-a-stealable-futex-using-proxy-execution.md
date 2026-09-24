---
id: sched-20260918-011
date: '2026-09-18'
subject: 'FUTEX_PING: A stealable futex using Proxy Execution.'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260917043339.2093426-1-suleiman@google.com>
lore_url: https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/
authors:
- Suleiman Souhlal
- John Stultz
maintainers_involved:
- Peter Zijlstra
- Steven Rostedt
- John Stultz
current_version: v1
patch_series:
- version: v1
  msgid: <20260917043339.2093426-1-suleiman@google.com>
  date: '2026-09-17'
  summary: RFC 00/12：可偷取 futex + Proxy Execution
  review_outcome: Peter 质疑 PI 严格性自洽、要求死锁检测器、倾向 mutex 路线
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 缺用户态死锁检测器（block 时返回 -EDEADLK）
  - 新 futex vs 复用 mutex 的路线未定
  - PI 严格性语义自洽问题
  next_action: 作者回应路线质疑并设计死锁检测后再推进
contribution_opportunities:
- kind: discussion
  description: 论证严格性应按调度类还是锁类型决定
- kind: review
  description: 评估用户态 futex 死锁检测器设计（block 时 vs schedule 时）
generated_at: '2026-09-19T09:00:00'
source_email_count: 6
related_articles:
- sched-20260917-012
tags:
- futex
- proxy_execution
title: 'FUTEX_PING: A stealable futex using Proxy Execution.'
layout: article
---

## TL;DR
增量更新：Suleiman Souhlal 的 FUTEX_PING（可偷取 futex + Proxy Execution，RFC 00/12）本日迎来密集高层讨论。Steven Rostedt 与 John Stultz 回溯了 FUTEX_PI 强制公平导致 SCHED_OTHER 性能崩溃、催生新 futex 的动机；Peter Zijlstra 指出"又想要 Priority Inheritance 又不想要 PI 严格性"自相矛盾，主张复用 mutex 的 FUTEX_LOCK/UNLOCK 路线，并强调整个 futex/proxy 需要死锁检测器（应在 block 时做、返回 -EDEADLK），明确"我们不急着合"。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-012-futex-ping-a-stealable-futex-using-proxy-execution.html">sched-20260917-012</a>：Google/Android 场景下少数 RT 任务与数百 SCHED_OTHER 任务竞争共享锁，FUTEX_PI 强制严格 PI/FIFO 语义导致 SCHED_OTHER 性能崩溃，需要一种"RT 保持 PI、SCHED_OTHER 可被偷取"的新 futex，并借助 Proxy Execution 由锁 owner 代为执行被阻塞的 waiter。

## 技术方案
沿用 RFC 方案：新增 FUTEX_PING（PING 名字是玩笑、可改），保留 waiter bit、支持 Proxy Execution，让公平任务可 steal 锁。本日讨论重心转向"是否该作为全新 futex op，还是复用 mutex 的 FUTEX_LOCK/UNLOCK + proxy"。

## 版本演进与当前进展
- v1（09-17，`<20260917043339.2093426-1-suleiman@google.com>`）：RFC 00/12 首版，本日无新版。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：① 直指自相矛盾——一边叫 "Priority Inheritance Next-Gen"、一边又不想要 PI/RT 的严格性，"鱼与熊掌不可兼得"；② FUTEX_LOCK/UNLOCK 本身是值得做的，Waiman 早前尝试死于缺乏 review；③ 对把 handoff 放在 futex 代码里不满（`mutex_unlock()` 已有）；④ 关键：整个 futex/proxy 需要死锁检测器，内核态不担心 lock 环，但用户态不可信——应在 block 时做而非 schedule() 时做，那是返回 `-EDEADLK` 的理想上下文；⑤ 严格性应该取决于调度类而非锁类型（可按 owner/waiter 类决定 steal 行为）；⑥ 对"vendor 已经在用 racy hack、不快点合就固化"的论调直言"这是勒索"，"我们不会因此赶工"。
- **Steven Rostedt**：回溯动机——FUTEX_PI 强制所有用户公平导致性能崩溃；建议 SCHED_OTHER 可不公平、更多放用户态；"FUTEX_PING"名字是玩笑可改；RT 任务必须保持公平否则无人用。
- **John Stultz**：认同 FUTEX_LOCK/UNLOCK 之名；指出 FUTEX_*_PI 的顾虑在语义（严格 RT 优先级 handoff）而非机制；vendor 已在 FUTEX_WAIT 未用字段里传 owner 做 boost（有竞态），说明需求迫切。
- **Suleiman Souhlal（作者）**：PING 与已存在的 "TP futex" 相似（后者写得更漂亮，差异在 waiter bit 与 rwlock 支持）；要 PI 不仅为 RT、也要公平任务间（sched group shares 场景），rtmutex 系 PI futex 无法覆盖，故走全新实现；关切用户态死锁会否触发内核 lockdep 告警。
- 分歧点：新 futex op vs 复用 mutex；严格性归属（锁类型 vs 调度类）；死锁检测器的实现位置与时序。

## 合入评估
*likelihood=low*。早期 RFC，Peter 明确"不急着合"，并要求引入死锁检测器、论证新 futex 与 mutex 路线取舍。*blocking_issues*：缺乏用户态死锁检测器；"新 futex vs mutex-based"路线未定；PI 严格性语义自洽问题。*next_action*：作者回应 Peter 的路线质疑（为何不能复用 mutex）、设计并实现 block 时的死锁检测，再谈推进。

## 效果评估
本日无新增 benchmark。Rostedt 提及历史上 FUTEX_PI 换性能大幅回退、SCHED_OTHER 不公平化后几乎回到普通 FUTEX 水平（Google 内部测试，未公开具体数字）。

## 我可以参与的点
- kind=discussion：就"严格性应按调度类还是锁类型决定"给出 sched 侧论证（这是 Peter 抛出的核心设计问题，尚无结论）。
- kind=review：评估用户态 futex 死锁检测器的可行设计（block 时 vs schedule 时的取舍，Peter 已倾向 block 时）。

## 参考链接
- lore（RFC cover）: https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/
