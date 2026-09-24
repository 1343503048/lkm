# sched: Allow sleeping spinlocks on PREEMPT_RT within non_block_start()/end block.

## TL;DR
Sebastian Siewior 的 v2（syzbot 报告）：`non_block_start()/end()` 为捕捉依赖锁/可睡眠条件的回调而引入，当初把 spinlock 排除在外。但 PREEMPT_RT 上 `spinlock_t`/`rwlock_t` 变成可睡眠自旋锁、带 `might_sleep()`，锁竞争时会 `schedule()`，于是在 `non_block` 块内触发 splat。修复给 `__might_resched()` 增加一个 `sleeping_lock` 参数，区分「来自可睡眠锁的调度请求」。已获 David Woodhouse Acked-by。

## 背景与问题
commit `312364f3534c ("kernel.h: Add non_block_start/end()")` 引入 `non_block_start()/end()`，意在捕获依赖锁或可睡眠条件的回调以保证前向进展；commit message 里把 spinlock 排除，理由是「spinlock 不可能对页面分配器有间接依赖」。但在 PREEMPT_RT 上，`spinlock_t` 与 `rwlock_t` 被变成可睡眠自旋锁（带 `might_sleep()`），锁竞争时可能 `schedule()`，于是在 `non_block` 计数非零的块内触发 splat。除 mm 外，pwm 也是 `non_block_start()` 的用户（hrtimer 在 RT 上可能获取 spinlock_t）。

## 技术方案
给 `__might_resched()` 增加 `sleeping_lock` 参数，标识该次调度请求是否来自可睡眠锁（true）还是普通调度请求（false）。修改判定为 `(rt_sleeping_lock || !current->non_block_count)`，即在 `non_block` 块内放行来自可睡眠锁的调度请求。`rtlock_might_resched()`（PREEMPT_RT 上两种可睡眠锁共用）传入 `true`；`cond_resched()`/`cond_resched_lock()` 等普通路径传 `false`。改动覆盖 `include/linux/kernel.h`、`include/linux/sched.h`、`kernel/locking/spinlock_rt.c`、`kernel/sched/core.c`。

## 版本演进与当前进展
- **v2**（本日 107822，`<20260916155105.qDi2MiYW@linutronix.de>`）：相对 v1 只是带齐标签重发——新增 `Reported-by: syzbot+c3178b6b512446632bac@syzkaller.appspotmail.com` 与 `Closes:` 指向 syzkaller bug、携带 David Woodhouse 的 Acked-by。
- v1 于 2026-08-21 发出。

## Maintainer 意见与讨论焦点
- **David Woodhouse**：已给 `Acked-by`。
- 无 NAK；本日暂无新的反对意见。

## 合入评估
*likelihood=medium*。syzbot 报告的明确 RT splat、方案清晰且已有 Acked-by，但改动横跨 kernel.h/sched.h 与调度核心的 `__might_resched()` 语义，需 RT/locking 维护者最终确认。*blocking_issues*：无实质阻塞。*next_action*：待 RT/locking 维护者收取。

## 效果评估
未给出量化数据；属 syzbot 触发的告警修复，目标是在 `non_block` 块内消除 RT 自旋锁的 splat。

## 我可以参与的点
- kind=testing：在 `CONFIG_PREEMPT_RT` + `CONFIG_DEBUG_ATOMIC_SLEEP` 下复跑 syzbot 用例，确认不再 splat、非 RT 路径无回归。
- kind=review：核对 `__might_resched()` 新增参数后所有调用点是否都正确传入 `false`、无遗漏或语义翻转。

## 参考链接
- v2 patch：https://lore.kernel.org/all/20260916155105.qDi2MiYW@linutronix.de/
- syzkaller bug：https://syzkaller.appspot.com/bug?extid=c3178b6b512446632bac

---
id: sched-20260916-019
date: '2026-09-16'
subject: 'sched: Allow sleeping spinlocks on PREEMPT_RT within non_block_start()/end block.'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: '<20260916155105.qDi2MiYW@linutronix.de>'
lore_url: 'https://lore.kernel.org/all/20260916155105.qDi2MiYW@linutronix.de/'
authors:
  - 'Sebastian Andrzej Siewior'
maintainers_involved: []
current_version: v2
patch_series:
  - version: v2
    msgid: '<20260916155105.qDi2MiYW@linutronix.de>'
    date: '2026-09-16'
    summary: '给 __might_resched() 加 sleeping_lock 参数，放行 RT 可睡眠自旋锁的调度请求'
    review_outcome: 'David Woodhouse Acked-by，重发补齐 syzbot 标签'
upstream_commit: null
fixes_commit: '312364f3534c'
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues: []
  next_action: '待 RT/locking 维护者收取'
contribution_opportunities:
  - kind: testing
    description: 'CONFIG_PREEMPT_RT 下复跑 syzbot 用例确认无 splat 且非 RT 无回归'
  - kind: review
    description: '核对新增参数后所有 __might_resched() 调用点传参正确'
generated_at: '2026-09-17T09:00:00'
source_email_count: 1
related_articles: []
tags:
  - preempt
---