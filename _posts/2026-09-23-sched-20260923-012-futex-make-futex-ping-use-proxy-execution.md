---
id: sched-20260923-012
subject: 'futex: Make FUTEX_*_PING use Proxy Execution.'
date: '2026-09-23'
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
current_version: v1
patch_series:
- version: v1
  msgid: <20260917043339.2093426-1-suleiman@google.com>
  date: '2026-09-17'
  summary: RFC 00/12：可偷取 futex + Proxy Execution
  review_outcome: Peter 质疑 PI 严格性、要求死锁检测器；Jihan LIN 本日呼应 block 时死锁检测 + -EDEADLK
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
  - 缺用户态死锁检测器
  - 新 futex vs mutex 路线未定
  - PI 严格性语义自洽问题
  next_action: 作者回应死锁检测设计与路线质疑
contribution_opportunities:
- kind: discussion
  description: 论证 block 时（sleep 前）死锁检测并返回 -EDEADLK 的实现可行性
- kind: review
  description: 评估 07/12 复用 owner walk 在争用路径的正确性与复杂度
generated_at: '2026-09-24T09:00:00'
source_email_count: 1
related_articles:
- sched-20260918-011
- sched-20260917-012
tags:
- proxy_execution
title: 'futex: Make FUTEX_*_PING use Proxy Execution.'
layout: article
---

## TL;DR
- sched-20260917-012：Suleiman Souhlal（Google，与 John Stultz 联合）发布 RFC 系列（12 枚），引入名为 PING（"PI Next Generation"）的新型 PI futex：可被偷取、内部用 Proxy Execution 而非 rtmutex，目标是让争锁者有机会不阻塞直接抢锁、并为 fair 任务带来优先级继承。Peter Zijlstra 认为整条路线「为时过早」（主张先让 rt_mutex 退化为普通 mutex），Jihan LIN 报告了一个会卡死 find_proxy_task() 的 ABBA 死锁场景。早期 RFC，短期无合入可能。
- sched-20260918-011：本日迎来密集高层讨论——Steven Rostedt 与 John Stultz 回溯 FUTEX_PI 强制公平导致 SCHED_OTHER 性能崩溃、催生新 futex 的动机；Peter 指出「又想要 PI 又不想要 PI 严格性」自相矛盾、主张复用 mutex 的 FUTEX_LOCK/UNLOCK 路线，强调整个 futex/proxy 需要死锁检测器（block 时做、返回 -EDEADLK），「我们不急着合」。
- sched-20260923-012（今天）：Jihan LIN 对 07/12 补丁给出设计意见——该方案可复用 owner walk 避免争用路径上的额外链式遍历，但「sleep 前做死锁检测」与 PI futex 更一致，且最后一次锁尝试若能直接向用户态返回 `-EDEADLK` 则额外遍历物有所值——与 Peter 先前「死锁检测应在 block 时做、返回 -EDEADLK」的立场呼应。

## 背景与问题
- sched-20260917-012：经典 PI futex 的严格 handoff 强制新争锁者排队，任何加锁都变成一次调度事件，对不需要严格 RT 语义的负载是性能损失。作者希望允许从 top waiter 偷取 futex；被偷取过多的任务可强制不可偷取地交接以避免饿死；用 Proxy Execution 让 fair 任务获得优先级继承（经典 PI futex 做不到）。
- sched-20260918-011：Google/Android 场景下少数 RT 任务与数百 SCHED_OTHER 任务竞争共享锁，FUTEX_PI 强制严格 PI/FIFO 导致 SCHED_OTHER 性能崩溃，需要「RT 保持 PI、SCHED_OTHER 可被偷取」的新 futex。
- sched-20260923-012（今天）：背景无新增。

## 技术方案
- sched-20260917-012：新 futex 类型 PING，owner 把 TID 写进 futex；内核允许 FUTEX_WAITERS 位 + 空 TID 同时存在以便偷锁；新增用户态原语 FUTEX_LOCK_PING/FUTEX_UNLOCK_PING；01/12 把 `task_struct->blocked_on` 从 `struct mutex *` 抽象为带类型标签的 `struct blocked_on_lock`；07/12 给 locker 侧设 proxy execution 位使阻塞任务可作 donor 执行；选择新建类型而非改造 PI futex。
- sched-20260918-011：沿用 RFC 方案，讨论重心转向「全新 futex op vs 复用 mutex 的 FUTEX_LOCK/UNLOCK + proxy」。
- sched-20260923-012（今天）：系列方案不变，讨论落在 07/12 的实现取舍——**Jihan LIN** 肯定「可复用 owner walk」避免争用 futex 路径上的额外链式遍历；但提出 sleep 前做死锁检测更贴近 PI futex，且若最后一次锁尝试能直接向用户态返回 `-EDEADLK`，额外的一次遍历就值得付出。

## 版本演进与当前进展
- v1（09-17，RFC 00/12）：12 枚 RFC，新 futex 类型 PING + Proxy Execution。本日无新版，为 07/12 的持续评审。

## Maintainer 意见与讨论焦点
本日为 Jihan LIN 的单条评审意见，无维护者新表态。其「sleep 前死锁检测 + 返回 -EDEADLK」的观点与 Peter Zijlstra 此前明确提出的「死锁检测应在 block 时做、那是返回 -EDEADLK 的理想上下文」方向一致，是对该设计点的社区侧呼应。分歧仍为 Peter 此前列出的路线问题（新 futex op vs 复用 mutex、严格性归属、死锁检测实现位置），未见收敛。

## 合入评估
*likelihood=low*。仍处早期 RFC，Peter 明确「不急着合」并要求死锁检测器与路线论证；本日新增意见强化了「block 时死锁检测 + -EDEADLK」这一设计点，但作者尚未回应。*blocking_issues*：缺用户态死锁检测器；「新 futex vs mutex-based」路线未定；PI 严格性语义自洽问题。*next_action*：作者回应死锁检测设计与路线质疑后才有推进空间。

## 效果评估
无本日新增 benchmark。历史上 Rostedt 曾以「FUTEX_PI 强制公平导致 SCHED_OTHER 性能崩溃」论证新 futex 的动机，本日未重复。

## 我可以参与的点
- kind=discussion：就「死锁检测应在 block 时（sleep 前）做并返回 -EDEADLK」给出具体实现可行性论证（Peter 与 Jihan 观点一致，但尚无落地设计）。
- kind=review：评估 07/12 复用 owner walk 的方案在争用路径上的正确性与复杂度，帮助作者回应 Jihan 的取舍。

## 参考链接
- lore（Jihan LIN 回复）: https://lore.kernel.org/all/d60be130-23eb-4e11-9bb0-1df0ec6ad42e@gmail.com/
- lore（RFC cover）: https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/
