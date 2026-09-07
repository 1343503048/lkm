# sched/cache: Fix use-after-free of the mm replaced by exec

## TL;DR

Hyunwoo Kim 8/30 发的单补丁修一个 CAS 记账路径上的 UAF：`account_mm_sched()` 在**别人的 rq** 上读 `rq->curr->mm`，而这个 mm 可能正被同任务的 `execve()` 换掉并释放。补丁的做法是在 `exec_mm_put_old()` 里 `mmput()` 之前插一次 `this_rq_lock_irq()` 锁环，充当"穷人版 `synchronize_rcu()`"。8/31 Chen Yu 认可该技巧（"A smart fix, learnt!"）但提出一个未决问题：**为什么不直接 `synchronize_rcu()`**，以免在重系统上抢 rq lock；另外追问 `kernel/events/core.c` 里那处 `guard(rcu)()` 是否与本 UAF 有关。

## 背景与问题

- **触发路径**：waker 无法使用 wakelist 时，`ttwu_queue()` 会去拿**目标 CPU** 的 rq lock，并沿 `enqueue_task_fair() → update_curr() → update_se() → account_mm_sched()` 走下去。此时传给 `account_mm_sched()` 的任务是**该 rq 上正在跑的任务**，不是被唤醒的那个；它读 `p->mm` 并更新 `mm->sc_stat`。
- **为什么是 UAF**：没有任何东西保证这个 mm 还活着——rq lock 与 `rq->cpu_epoch_lock` 与 mm 的生命周期无关。若该任务恰在 `execve()` 中，`exec_mmap()` 会把 `tsk->mm`/`tsk->active_mm` 指向新 mm，`setup_new_exec()` 里的 `exec_mm_put_old()` 丢掉旧的一个（`exec()` 失败时 `free_bprm()` 同理）；从 `mmput()` 走到 `__mmdrop()` 时，`mm_destroy_sched()` 对 `sc_stat.pcpu_sched` 调 `free_percpu()`，`free_mm()` 归还 `mm_struct`。已经读到旧指针的一方会继续用：往**已释放的 per-cpu 区**累加 runtime、读**已释放的 mm_struct** 里的 `sc_stat`，条件合适时还会写 `sc_stat.cpu`。
- **为什么之前的修复没覆盖**：commit `9f23469401b0` ("sched/cache: Fix potential NULL mm pointer access") 把残留的 `p->mm` 解引用改成本地变量，并声称 active_mm 引用会让结构体保持分配。这对其他 detach mm 的路径成立（它们拿 `mmgrab_lazy_tlb()` 引用），但 `exec` 把 `active_mm` 也一并换成新 mm，那份引用就没了；剩下的只有 `bprm->old_mm` 的 `mm_users` 引用，而丢掉它的正是那次释放。
- **架构/配置相关**：需要 CAS 开启（`CONFIG_SCHED_CACHE` 一类），跨 CPU 唤醒与 `execve()` 并发。

## 技术方案

diffstat：`fs/exec.c |1+`、`include/linux/sched.h |4+`、`kernel/events/core.c |2+`、`kernel/sched/fair.c |16+`（共 23 行新增）。

核心是在释放旧 mm 之前制造一次与读者相同的锁序，从而把远程读者"过一遍"：

```c
/* exec() has switched to the new mm and is about to drop the old one. */
void sched_cache_exec_done(void)
{
        struct rq_flags rf;
        struct rq *rq;

        /*
         * account_mm_sched() dereferences rq->curr->mm under this rq's lock,
         * so a remote CPU can still be using the old mm. The lock cycle waits
         * for it, and the store to tsk->mm cannot be reordered past the
         * release, so later acquirers see the new mm.
         */
        rq = this_rq_lock_irq(&rf);
        ...
}
```

调用点插在 `exec_mm_put_old()` 中 `mmput(old_mm)` 之前；`include/linux/sched.h` 里同时给出 `!CONFIG` 时的空 `static inline`。设计取舍很明确：**借用 rq lock 的 acquire/release 传递性来替代一个显式 RCU 宽限期**，好处是不引入阻塞式宽限期、语义与读者完全对齐；代价是每次 `exec` 都要过一次本 rq 的锁环。

系列里还捎带了一处 `kernel/events/core.c: attach_task_ctx_data()` 的 `guard(rcu)()`（注释写"old 只有在下面积 `try_cmpxchg()` 下才稳定"）——Chen Yu 本日专门问这处是否与本 UAF 相关，作者未在当日线程中回答。

## 版本演进与当前进展

- 8/30：v1（`<apPb-Dr4nPYuHQOK@v4bel>`），作者 Hyunwoo Kim。
- 8/31 12:22：Chen Yu 提出两点（见下节）。**本日内作者未回复、未发 v2**。
- 讨论仍在 v1 阶段，尚无 `Reviewed-by`/`Acked-by`。

## Maintainer 意见与讨论焦点

Chen Yu（CAS/Intel 侧，属该代码的实质维护者角色）两条，一条是认可、一条是关键分歧：

- 认可技巧本身："A smart fix, learnt! It behaves like a `synchronize_rcu()` to protect against the read in `account_mm_sched()`."
- **未解决的方案分歧**："since the context of invoking `account_mm_sched()` is preemption-disabled, I wonder if we can simply use `synchronize_rcu()` directly instead of `this_rq_lock_irq()` - just to avoid contention for rq-lock in heavy system?" 也就是说，如果 RCU 语义就够用，那么这个方案就不该在 exec 热路径上抢 rq lock。这一条决定了最终实现形态，且当天没人回答。
- 范围质疑：`kernel/events/core.c` 的 `guard(rcu)()` 是否属于本问题——隐含的意思是"不相关的改动应该拆成独立补丁"。

## 合入评估

**possible**。UAF 本身论证充分（有明确 CPU0/CPU1 时序图、有对 `9f23469401b0` 为何不够的解释、`Fixes:` 类元数据在当日可见文本中未出现），CAS 代码的作者本人认可修复方向，因此"要修"没有争议。卡点是**修法**：`synchronize_rcu()` vs `this_rq_lock_irq()` 的选择还没结论，且混入的 perf 侧改动需要拆分或被证明相关。`next_action`：作者回应 Chen Yu 的问题（并说明 `account_mm_sched()` 的 preemption-disabled 上下文能否被 `synchronize_rcu()` 正确覆盖）、把 `kernel/events/core.c` 那处拆走或说明理由。

## 效果评估

暂无效果数据。当日线程内没有复现程序、没有 KASAN 报告、没有性能对比；Chen Yu 关于"避免重系统 rq-lock 争抢"的担忧同样是**定性判断，未见数据**。

## 我可以参与的点

- **回答 Chen Yu 的问题**：在 `exec_mm_put_old()` 的上下文里用 `synchronize_rcu()` 是否安全且足够（读者处于 preemption-disabled 的非阻塞区间时 RCU 宽限期是否真的覆盖它）——这是一个纯语义问题，谁先给出带论证的回帖谁就定形了方案。
- **量化 exec 路径开销**：`this_rq_lock_irq()` 锁环放在 exec 上，对 fork/exec 密集型负载（容器、CI）是可以直接测的，给出数据能实质推进讨论。
- **回合风险自查**：若目标分支带 CAS，`account_mm_sched()` 跨 CPU 读 `rq->curr->mm` 这一形态是否同样存在值得核对；本 bug 的前提（waker 走 `ttwu_queue()` 拿目标 rq 锁并下探 `update_curr()`）在不同分支上路径深度可能不同。
- **帮忙补 repro**：线程里没有 KASAN 复现，写一个"pipe write 唤醒 + 同任务 exec"的竞争程序并回帖，对这类 UAF 的收口最快。

## 参考链接

- lore thread（v1 补丁）: https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/
- Chen Yu 本日意见: https://lore.kernel.org/all/825d9dcc-b052-4367-a9c7-15efc4b354f8@intel.com/
- 相关前置修复: commit `9f23469401b0` ("sched/cache: Fix potential NULL mm pointer access")
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260831-009
date: '2026-08-31'
subject: "sched/cache: Fix use-after-free of the mm replaced by exec"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<apPb-Dr4nPYuHQOK@v4bel>"
lore_url: "https://lore.kernel.org/all/825d9dcc-b052-4367-a9c7-15efc4b354f8@intel.com/"
authors: [Hyunwoo Kim, Chen Yu]
maintainers_involved: [Chen Yu]
current_version: v1
patch_series:
  - version: v1
    msgid: "<apPb-Dr4nPYuHQOK@v4bel>"
    date: 2026-08-30
    summary: "在 exec_mm_put_old() 释放旧 mm 前用 sched_cache_exec_done()/this_rq_lock_irq() 锁环等待远程 CPU 完成 account_mm_sched() 对 rq->curr->mm 的读取"
    review_outcome: "Chen Yu 认可技巧但要求论证能否改用 synchronize_rcu() 以避免 rq-lock 争抢，并追问 perf 侧 guard(rcu) 是否与本问题相关"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: possible
  blocking_issues:
    - "synchronize_rcu() 是否可替代 this_rq_lock_irq() 尚无结论（涉及 account_mm_sched() 的 preemption-disabled 上下文语义）"
    - "kernel/events/core.c 的 guard(rcu)() 与本 UAF 的关联性未被作者说明，可能要求拆分为独立补丁"
    - "无 KASAN 复现、无性能数据、无 Fixes 标签（当日可见文本中未出现）"
  next_action: "作者需回答 Chen Yu 的 synchronize_rcu() 问题并拆出不相关的 perf 改动"
contribution_opportunities:
  - kind: discussion
    description: "论证在 exec_mm_put_old() 上下文中 synchronize_rcu() 能否覆盖 preemption-disabled 的 account_mm_sched() 读者，从而替代 rq lock 锁环"
  - kind: testing
    description: "测量 this_rq_lock_irq() 锁环对 fork/exec 密集型负载（容器/CI）的开销，为两种修法提供依据"
  - kind: testing
    description: "构造 pipe-write 唤醒与同任务 execve 并发的 KASAN 复现程序并回帖"
generated_at: "2026-09-07T21:16:22"
source_email_count: 1
related_articles: []
tags: [load_balance, crash]
---
