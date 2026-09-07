# sched/cache: Fix use-after-free of the mm replaced by exec

## TL;DR

Hyunwoo Kim 单补丁修 cache-aware scheduling 记账路径上的一个 slab-use-after-free：`account_mm_sched()` 会在**别人的 rq** 上读 `rq->curr->mm` 并写 `mm->sc_stat`，而这个 mm 可能正被同一次 `execve()` 换掉并释放；补丁的做法是在 `exec_mm_put_old()` 真正 `mmput()` 之前插一次 `this_rq_lock_irq()` 的锁环，当作"穷人版 `synchronize_rcu()`"。作者给了完整 KASAN 报告（读侧 `update_se()`、释放侧 `setup_new_exec()`）与 CPU0/CPU1 时序图，带 `Fixes: df0d98475954` 和 `Cc: stable`。当天无人回复；次日 Chen Yu 认可技巧但追问"为什么不直接 `synchronize_rcu()`"（见 sched-20260831-009）。

## 背景与问题

- **触发路径**：waker 无法使用 wakelist 时，`ttwu_queue()` 会去拿**目标 CPU** 的 rq lock，然后沿 `enqueue_task_fair() → update_curr() → update_se() → account_mm_sched()` 走下去。此时 `account_mm_sched()` 看到的是**那个 rq 上正在跑的任务**（不是被唤醒的任务），它读 `p->mm` 并更新 `mm->sc_stat`。
- **为什么是 UAF**：rq lock 与 `rq->cpu_epoch_lock` 跟 mm 的生命周期**没有任何关系**。若该任务恰在 `execve()` 中，`exec_mmap()` 把 `tsk->mm`/`tsk->active_mm` 都指向新 mm，`setup_new_exec()` 里的 `exec_mm_put_old()` 丢掉旧引用（`exec` 失败时 `free_bprm()` 同理）；`mmput() → __mmdrop()` 时 `mm_destroy_sched()` 对 `sc_stat.pcpu_sched` 调 `free_percpu()`，`free_mm()` 归还 `mm_struct`。已经读到旧指针的一方会继续往**已释放的 per-cpu 区**累加 runtime、读**已释放的 mm_struct** 里的 `sc_stat`，条件合适时还会写 `sc_stat.cpu`。
- **为什么之前的修复没盖住**：`9f23469401b0`（"sched/cache: Fix potential NULL mm pointer access"）把残留的 `p->mm` 解引用改成本地变量，并声称 active_mm 引用能保证结构体存活。这对其他 detach mm 的路径成立（它们拿 `mmgrab_lazy_tlb()` 引用），但 `exec` 把 `active_mm` 也一并换成新 mm，那份引用就没了——剩下的只有 `bprm->old_mm` 的 `mm_users` 引用，而丢掉它的正是那次释放。
- **KASAN 现场**（作者提供）：`BUG: KASAN: slab-use-after-free in update_se+0xe6e/0xf70`，`Read of size 8 ... by task sc-direct-set/80`，读侧栈 `update_se → update_curr → enqueue_task_fair → enqueue_task → ttwu_do_activate → try_to_wake_up → ... → anon_pipe_write`（即"写 pipe 唤醒对端"触发的跨 CPU 唤醒）；释放侧 `Freed by task 1`：`kmem_cache_free → setup_new_exec → load_elf_binary → bprm_execve → do_execveat_common → __x64_sys_execve`；对象属于 `mm_struct` slab（size 1688），越界点在该 freed region 内偏移 400 字节。
- **配置前提**：需要开启 CAS（`CONFIG_SCHED_CACHE` 路径），并让"跨 CPU 唤醒"与 `execve()` 真正并发。

## 技术方案

在 `exec_mm_put_old()` 里 `mmput(old_mm)` 之前做一次本 CPU 的 rq 锁环：

```c
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
	rq_unlock_irq(rq, &rf);
}
```

论证链条（作者原话整理）：读侧那个任务就是**该 rq 的 curr**，所以是同一把锁；如果这中间任务迁到了别的 CPU，**离开那个 rq 本身就需要同一把锁**，因此那个 CPU 上的读者必然已经结束。而这个读者只在 rq lock 内使用 mm、从不把指针外传，所以"拿到过锁"就意味着"它用完了"，之后任何拿锁者看到的都是新的 `tsk->mm`。

改动共 +23 行：`fs/exec.c` 加一次调用、`include/linux/sched.h` 导出/空实现 `sched_cache_exec_done()`、`kernel/sched/fair.c` 放实现，**另外还夹了一处看起来不同源的改动**——`kernel/events/core.c` 的 `attach_task_ctx_data()` 里给 `try_cmpxchg(&task->perf_ctx_data, ...)` 循环加 `guard(rcu)()`（注释：`@old ... is only stable under RCU`）。

**未采用的方案**：作者没有用 `mmgrab_lazy_tlb()`/引用计数把旧 mm 钉住，也没用真正的 `synchronize_rcu()`；选锁环的理由是它只等一次 rq lock 轮转，代价远低于 grace period。（次日 Chen Yu 正是质疑这个取舍。）

## 版本演进与当前进展

- 8/30 15:30（北京时间）v1 发出，当日**无人回复**、无 Reviewed-by/Tested-by。
- 次日线程开始滚动：Chen Yu 认可技巧（"A smart fix, learnt!"）但问为什么不直接 `synchronize_rcu()`、并追问 `kernel/events/core.c` 那处 `guard(rcu)()` 是否与本 UAF 有关；后续 v2 于 9/1 出现（见 sched-20260831-009 与 9 月的几篇增量文）。本文只覆盖 v1 当日状态。

## Maintainer 意见与讨论焦点

- 当日**没有 CAS 维护者（Tim Chen / Chen Yu）表态**，这是唯一的事实：一个带 `Cc: stable` 的 UAF 修复在 24 小时内无人认领。
- 从补丁本身可以预判的争点（次日也确实被提出）：
  1. **`this_rq_lock_irq()` 当 grace period 用的正确性论证是否成立**——它依赖"读侧只在 rq lock 内碰 mm、不外传指针"这一强前提；只要有任何一条读路径把 `mm` 指针带到锁外（例如缓存到局部变量后再用），整个推理就失效。
  2. **开销与可维护性**：为什么不用 `synchronize_rcu()`；重系统上抢 rq lock 会不会引入不确定的停顿。
  3. **一个补丁混两件事**：`kernel/events/core.c` 的 RCU 修复与本 UAF 是否同源问题，是否该拆开各自带 `Fixes:`。

## 合入评估

**possible**（偏正面）。`Fixes:` 指到 CAS 的基础设施提交 `df0d98475954`、带 `Cc: stable`、有完整 KASAN 证据，且改法只有 23 行、非侵入（只在 `exec` 路径加一次锁环）——这类修复通常会被 CAS 作者接走。真正的门槛是上面第 1 点：需要在邮件里把"没有任何读者把 mm 指针带出 rq lock"这条不变式证明清楚，否则维护者会倾向选一个有明确引用计数语义的做法。**尚未进 tip/stable（未获取到）**。

## 效果评估

只有复现证据，没有性能数据。作者给出了 KASAN 报告与 CPU0/CPU1 交错时序（含具体偏移与 task 名 `sc-direct-set/80`、释放者 PID 1），足以证明缺陷真实存在；但**没有给出触发频率、命中率，也没有测量那次 rq 锁环的开销**——对 `exec` 热路径（进程启动密集的容器场景）的影响属于未评估项。

## 我可以参与的点

- **验证不变式**：把所有 `account_mm_sched()`/CAS 相关读取 `p->mm` 或 `rq->curr->mm` 的路径列一遍，确认没有读者在 rq lock 之外持有 mm 指针，回帖给出结论（这是这个补丁成立与否的核心，目前邮件里无人做）。
- **量化锁环开销**：在容器/`exec` 密集负载（如并行构建、大量短生命周期进程）上测 `execve()` 延迟与 system 时间前后差异，回应"为什么不用 `synchronize_rcu()`"的成本问题；这类数据 CAS 作者会直接用。
- **拆补丁建议**：`kernel/events/core.c` 的 `guard(rcu)()` 与本 UAF 无直接因果，可以建议作者拆成独立补丁、各自带 `Fixes:`——这类"顺带修"在上游通常会被要求分开。
- **回合判断**：若 OLK-6.6 回合过 CAS 基础设施（`df0d98475954` 一类），本条属于必跟的稳定修复；等 v2 定型后再动，届时 `Fixes:` 需改写指向 OLK-6.6 自己的 commit。

## 参考链接

- lore thread（v1，当日唯一邮件）: https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/
- 本补丁 `Fixes:` 目标: `df0d98475954` ("sched/cache: Introduce infrastructure for cache-aware load balancing")
- 前一次相关修复: `9f23469401b0` ("sched/cache: Fix potential NULL mm pointer access")
- tip-bot commit: 未获取到
- stable backport: 未获取到（仅 `Cc: stable@vger.kernel.org`）

---
id: sched-20260830-002
date: '2026-08-30'
subject: "sched/cache: Fix use-after-free of the mm replaced by exec"
subsystem: sched
type: bug
status: under_review
severity: high
thread_root_msgid: "<apPb-Dr4nPYuHQOK@v4bel>"
lore_url: "https://lore.kernel.org/all/apPb-Dr4nPYuHQOK@v4bel/"
authors: [Hyunwoo Kim]
maintainers_involved: [Tim Chen, Chen Yu]
current_version: v1
patch_series:
  - version: v1
    msgid: "<apPb-Dr4nPYuHQOK@v4bel>"
    date: 2026-08-30
    summary: "在 exec_mm_put_old() 丢弃旧 mm 前插入 this_rq_lock_irq() 锁环充当穷人版 synchronize_rcu()，堵住 account_mm_sched() 跨 CPU 读已释放 mm 的 UAF；附带在 perf 的 attach_task_ctx_data() 加 guard(rcu)()"
    review_outcome: "v1 刚发出，当日暂无 review 意见；次日 Chen Yu 认可但质疑不用 synchronize_rcu() 的取舍"
upstream_commit: null
fixes_commit: "df0d98475954"
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "未证明'没有任何读者把 mm 指针带出 rq lock'这一不变式，锁环方案的成立依赖它"
    - "未评估 exec 路径上多做一次 rq 锁轮转的开销"
    - "kernel/events/core.c 的 RCU 修复与本 UAF 无因果关系，可能被要求拆补丁"
  next_action: "作者需列出所有 mm 读取路径的持锁证明并补开销数据，同时拆分 perf 侧改动"
contribution_opportunities:
  - kind: review
    description: "逐条核对 CAS 中读取 p->mm/rq->curr->mm 的路径是否都在 rq lock 内且不外传指针，回帖给出不变式证明"
  - kind: testing
    description: "在 exec 密集的容器负载上测量该 rq 锁环对 execve 延迟与 system 时间的影响"
  - kind: discussion
    description: "建议把 kernel/events/core.c 的 guard(rcu)() 拆成独立补丁并补自己的 Fixes 标签"
generated_at: "2026-09-07T22:06:23"
source_email_count: 1
related_articles: [sched-20260831-009]
tags: [load_balance, crash]
---
