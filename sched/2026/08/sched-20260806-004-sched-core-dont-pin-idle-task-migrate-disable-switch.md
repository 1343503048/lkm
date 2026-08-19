# sched/core: Don't pin the idle task in migrate_disable_switch()

# sched/core: 不要在 migrate_disable_switch() 中钉住 idle 任务（真实 panic 修复）

## 摘要

Krystian Slowik 报告并修复了一个**真实内核 NULL 指针解引用 panic**，已在两台 x86-64 生产机（Ubuntu 7.0.0-28，PREEMPT(lazy)）复现。

Root cause：
- commit `650952d3fb38`（「sched: Make __do_set_cpus_allowed() use the sched_change pattern」）使 `do_set_cpus_allowed()` 在目标任务 on_rq 时通过 `sched_change` guard 做 dequeue/re-enqueue。
- idle 任务算 on_rq（`init_idle()` 设 `idle->on_rq = TASK_ON_RQ_QUEUED`），但 idle sched class **没有真正的 `dequeue_task()`（只有会丢锁再取锁的 "bad: scheduling from the idle thread!" 调试桩）也没有 `enqueue_task()`**，于是在 idle 任务上跑该 guard 时，`sched_change_end()` 跳进 NULL 的 `enqueue_task` 指针 → RIP 0x0 panic。
- commit `942b8db96500`（「sched: Fix migrate_disable_switch() locking」）把 `migrate_disable_switch()` 移到 `__schedule()` 顶部，使其在 idle 循环的**每次** schedule-out 都跑（而非仅真实上下文切换），因此只要 idle 循环里持有一个未释放的 `migrate_disable()`（如 tracing/BPF 回调），idle 任务 schedule 时即触发钉住路径。

修复：在 `migrate_disable_switch()` 里对 `p == rq->idle` 直接 return（per-CPU idle 任务永不迁移，无需钉住）。用 `p == rq->idle` 而非 `is_idle_task()`，因为后者还匹配 `PF_IDLE` 的 idle-injection 线程（普通可排队任务）。

## 技术细节

修复 diff（示意）：
```
static void migrate_disable_switch(struct rq *rq, struct task_struct *p)
{
    if (p->cpus_ptr != &p->cpus_mask)
        return;
+   /* The per-CPU idle task never migrates, there is nothing to pin. */
+   if (p == rq->idle)
+       return;
    scoped_guard (task_rq_lock, p)
        do_set_cpus_allowed(p, &ac);
}
```

`Fixes: 650952d3fb38`，`Cc: stable@vger.kernel.org # v7.0+`。

## 影响与风险

- 影响面：sched/core 的 `migrate_disable_switch()`，idle 循环路径；影响所有在 idle 回调中持 `migrate_disable` 的配置（tracing/BPF）。
- 风险：高（作为 bug 严重度）—— 真实生产 panic。修复局部、保守（仅跳过 idle 任务），并顺带使 `___migrate_enable()` 对 idle 任务不可达，逻辑自洽。
- 收益：消除 idle 循环 NULL 解引用 panic。

## 评价

明确的真实 bug + 精准最小修复 + stable 标记，合入可能性高。已带 Fixes/stable，建议优先进 tip/sched/urgent。是 08-06 最值得关注的 fix 之一。

---
subject: "sched/core: Don't pin the idle task in migrate_disable_switch()"
id: sched-20260806-004
date: "2026-08-06"
title: "sched/core: 不要在 migrate_disable_switch() 中钉住 idle 任务（真实 panic 修复）"
series: "sched/core: Don't pin the idle task in migrate_disable_switch()"
type: fix
status: under_review
severity: high
merge_likelihood: high
tags: [preempt, topology]
authors: ["Krystian Slowik <me@krystianslowik.com>"]
reviewers: ["Peter Zijlstra <peterz@infradead.org>"]
related_articles: []
emails: ["uid-24051@qq-imap", "uid-23936@qq-imap"]
---
