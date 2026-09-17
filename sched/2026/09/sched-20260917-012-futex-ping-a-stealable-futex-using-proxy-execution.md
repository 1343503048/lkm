# FUTEX_PING: A stealable futex using Proxy Execution.

## TL;DR
Suleiman Souhlal（Google，与 John Stultz 联合）发布 RFC 系列（12 枚），引入名为 PING（"PI Next Generation"，Steven Rostedt 命名）的新型 PI futex：可被偷取、内部用 Proxy Execution 而非 rtmutex。目标是让争锁者有机会不阻塞直接抢锁，并为 fair 任务带来优先级继承。Peter Zijlstra 认为整条路线"为时过早"（主张先让 rt_mutex 退化为普通 mutex），并担心无界 proxy 链与死锁；Jihan LIN 报告了一个会卡死 find_proxy_task() 的 ABBA 死锁场景。属早期 RFC，短期无合入可能。

## 背景与问题
经典 PI futex 的严格 handoff 会强制新的争锁者排队等待，任何加锁操作都变成一次调度事件。对不需要严格 RT 语义的负载，这是性能损失。作者希望允许从 top waiter 偷取 futex，让争锁者有机会不阻塞拿到锁；被偷取过多的任务可强制不可偷取地交接锁以避免饿死。用 Proxy Execution 还能让 fair 任务获得优先级继承（经典 PI futex 做不到）。

## 技术方案
- 新 futex 类型 PING，用法类似 FUTEX_*_PI，owner 把 TID 写进 futex。
- 与普通 PI futex 的可见差异：内核允许 FUTEX_WAITERS 位 + 空 TID 同时存在，以便新争锁者从 top waiter 偷锁；用户态可观察到 futex 已解锁但有 waiter 时不经内核直接偷取。
- 新增用户态原语 FUTEX_LOCK_PING / FUTEX_UNLOCK_PING。
- 01/12 把 `task_struct->blocked_on` 从 `struct mutex *` 抽象为带类型标签的 `struct blocked_on_lock`（BO_T_NONE/BO_T_MUTEX/BO_T_PING_FUTEX），供 futex 复用。
- 07/12 给 locker 侧设置 proxy execution 位，使阻塞在 PING futex 上的任务可作为 donor 执行。
- 选择新建 futex 类型而非改造 PI futex/rtmutex：PI futex 有严格 rtmutex 语义，为 RT 负载重要，但可能给不需要这些语义的负载带来性能损失。

## 版本演进与当前进展
v1（RFC，09-17，`<20260917043339.2093426-1-suleiman@google.com>`）刚发出，已收到 Peter Zijlstra、Jihan LIN、K Prateek Nayak 的回复。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra（00/12）**：最终目标是把 rt_mutex 删掉、让它退化为普通 mutex，届时现有 FUTEX_*_PI 会"自动生效"；因此认为"整条路线都为时过早"，并指了 Waiman Long 更早的 lazy-PI futex 工作。
- **Peter Zijlstra（07/12）**：建议仍保留硬编码的链长上限（在序列标记之外），否则用户态可构建任意长度的 proxy 链；还需能返回 -EDEADLK；理想情况下用户态在阻塞时多做一次图遍历，而不是依赖 pick 时的 sanity check。
- **Jihan LIN（07/12）**：发现 ABBA 死锁会演变成内核 lockup——A 拿 F1 后 futex(F2, LOCK_PING)、B 拿 F2 后 futex(F1, LOCK_PING)，两任务互阻且 `task_is_blocked()` 均为真，`find_proxy_task()` 会持 rq->lock 无限 A→B→A 遍历；建议在 find_proxy_task() 处理环或像 rtmutex 一样做链式死锁检测。
- **K Prateek Nayak（07/12）**：指向 08 月的相关既有系列（soolaugust）供对照。
- 分歧点：路线时机（Peter 认为 premature）、无界链与死锁检测缺失。

## 合入评估
likelihood=low。RFC 阶段，维护者明确认为为时过早，且存在死锁/无界链等未解决的正确性问题。blocking_issues：Peter 认为在 rt_mutex 退化为普通 mutex 之前为时过早；find_proxy_task 环遍历死锁待解决；无界 proxy 链需硬上限与 -EDEADLK。next_action：作者回应 Peter 的时机质疑，补环检测与链长上限后重新寻求对齐。

## 效果评估
无性能数据；作者以"避免把每次加锁变成调度事件"作为动机，未见 benchmark。

## 我可以参与的点
- kind=discussion：评估"偷取式 futex"与 Peter 主张的"rt_mutex 退化为普通 mutex"两条路线，给出在已有 PI futex 生态下的取舍分析。
- kind=new_patch：按 Jihan LIN 的复现实现 find_proxy_task() 的环检测（或链式死锁检测）补丁，作为对该 RFC 的实质贡献。
- kind=testing：复现 ABBA 死锁场景，验证环检测/硬上限是否消除 lockup。

## 参考链接
- lore（RFC cover）: https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/
- Peter 的时机质疑: https://lore.kernel.org/all/20260917085805.GD2009045@noisy.programming.kicks-ass.net/

---
id: sched-20260917-012
date: '2026-09-17'
subject: 'FUTEX_PING: A stealable futex using Proxy Execution.'
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: '<20260917043339.2093426-1-suleiman@google.com>'
lore_url: 'https://lore.kernel.org/all/20260917043339.2093426-1-suleiman@google.com/'
authors:
  - 'Suleiman Souhlal'
  - 'John Stultz'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20260917043339.2093426-1-suleiman@google.com>'
    date: '2026-09-17'
    summary: 'PING futex：可偷取的 PI futex，内部用 Proxy Execution，12 枚 RFC'
    review_outcome: 'Peter 认为 premature，Jihan 报死锁，Prateek 指向既有系列'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: low
  blocking_issues:
    - 'Peter 认为在 rt_mutex 退化为普通 mutex 之前为时过早'
    - 'find_proxy_task 环遍历死锁待解决'
    - '无界 proxy 链需硬上限与 -EDEADLK'
  next_action: '作者回应时机质疑并补环检测与链长上限'
contribution_opportunities:
  - kind: discussion
    description: '评估偷取式 futex 与 rt_mutex 退化路线的关系'
  - kind: new_patch
    description: '实现 find_proxy_task 环检测/链式死锁检测补丁'
  - kind: testing
    description: '复现 ABBA 死锁验证环检测是否消除 lockup'
generated_at: '2026-09-18T09:00:00'
source_email_count: 7
related_articles: []
tags:
  - proxy_execution
---