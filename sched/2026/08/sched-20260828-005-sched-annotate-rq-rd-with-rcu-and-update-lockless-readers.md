# sched: Annotate rq->rd with __rcu and update lockless readers

## TL;DR

**本文为增量更新**（完整背景见 sched-20260827-001）。Aaron Tomlin 的 6 补丁系列在一天之内连发 **v8 与 v9**：给 `struct rq->rd` 补上 `__rcu` 标注，并把 `kernel/sched/` 里所有无锁直读 `rq->rd` 的地方换成统一 helper。v8 按 Peter Zijlstra 对 v7 的意见引入 `rcu_dereference_root_domain()`；发完 v8 约 1 小时后作者自己回帖 "Please ignore"——Sashiko 机器人查出 `dl_task_needs_bw_move()` 在只持 `cpuset_mutex` 的进程上下文里解引用（既无 `sched_domains_mutex` 也无 RCU 读侧临界区），他用 virtme-ng 复现出 `WARNING: suspicious RCU usage`，随后 v9 补上 `guard(rcu)()` 与另外三处遗漏。8/28 当日 v9 无人回帖，但**作者自曝的缺陷恰好说明该系列的真正难点不是标注本身，而是"哪些上下文算合法读侧"**。

## 背景与问题

`struct rq` 的 `rd`（`root_domain` 指针）会被动态改写，旧对象的释放通过 `rq_attach_root()` 里的 `call_rcu()` 延迟。问题有两层：

1. `rd` 字段**缺少 `__rcu` 编译器标注**，因此 Sparse 无法校验任何解引用；
2. `kernel/sched/` 里多处无锁读者直接写 `rq->rd->...`，没有用 RCU 解引用原语——按 commit message 的说法，这意味着缺少跨架构正确所需的数据依赖屏障，并且在 `CONFIG_PROVE_RCU` 下产生虚假 Lockdep 告警。

受影响的读者分布在 `core.c`/`deadline.c`/`fair.c`/`rt.c`/`syscalls.c`/`topology.c`，包括 `set_rq_online()`/`set_rq_offline()` 里的 `rq->rd->online`、`add_nr_running()` 里的 `set_rd_overloaded(rq->rd, 1)`、`__sched_setscheduler()` 里的 `rq->rd->span` 与 `rq->rd->dl_bw.bw`、`dl_task_check_affinity()`、`dl_task_needs_bw_move()` 等。

## 技术方案

- `sched.h` 给 `rd` 加 `__rcu`；`sched_init()` 里的 `rq->sd = NULL; rq->rd = NULL;` 改成 `RCU_INIT_POINTER()`。
- 新增宏 **`rcu_dereference_root_domain(p)`**，在 `sched_domains_mutex` 或活跃的 RCU-sched 读侧临界区内做校验式解引用。作者对为什么再造一个与 `rcu_dereference_sched_domain()` 机制等价的宏给出的理由很明确：**代码可读性**——保持 `struct rq` 里 `rq->rd` 与 `rq->sd` 的命名对称，并且便于 grep。
- 系列其余 5 个补丁是配套的正确性/可用性改动：2/6 保护 `print_dl_rq()` 里对 `rq->rd` 的无锁访问，3/6 保护 `print_cpu()` 里对 `rq->curr` 的无锁访问，4/6 保护 `sched_show_numa()` 里的 `p->mm` 访问，5/6 让 `print_cfs_stats()` 用 `list_for_each_entry_rcu()`，6/6 新增 **per-CPU debugfs 文件** `/sys/kernel/debug/sched/cpu/cpu<N>/debug`（离线 CPU 返回 `-ENODEV`）。

为什么选"统一 helper 宏"而不是"逐点用 `rcu_dereference_sched()`/`rcu_access_pointer()`"：v7 的做法被 Peter 否掉，理由有三条——`rcu_dereference_protected()` 只该用于更新侧；`rq->lock` **不是**拓扑/root domain 的更新侧锁；`&rq->__lock` 直接引用破坏了 `rq_lock()` 抽象；而且逐点写法"far too verbose to endlessly repeat"。所以 v8 起改为单一宏，把 `sched_domains_mutex` 这一"真正的更新侧锁"编码进校验条件。

## 版本演进与当前进展

- **v7（8/27 06:42）**：逐点使用 `rcu_dereference()`/`rcu_dereference_sched()`/`rcu_access_pointer()`，6 文件 113 增 84 删。当天 Peter Zijlstra 三条意见（见下节），Vincent Guittot 指出误删了函数上方注释，作者承认是在改用 `rcu_dereference_sched()` 时无意丢的。
- **v8（8/28 03:40）**：引入 `rcu_dereference_root_domain()` 并全面替换读者，commit message 相应重写；6 文件 120 增 87 删。
- **v8 自撤（8/28 04:37）**：作者回帖 "Hi Peter, Vincent, Please ignore; I will address this in the next iteration."，说明 Sashiko 报出 `dl_task_needs_bw_move()` 的非法解引用上下文，并用 virtme-ng 在 `7.2.0-rc7-virtme-00041-g6509e33120f4` 上确认：

  ```
  WARNING: suspicious RCU usage
  kernel/sched/deadline.c:3366 suspicious rcu_dereference_check() usage!
  ```

  他还指出"对 `__rcu` 指针的直接解引用仍需转换"。
- **v9（8/28 06:18，约 1.5 小时后）**：`dl_task_needs_bw_move()` 外面套 `guard(rcu)()`；新增 `kernel/sched/syscalls.c` 改动（`__sched_setscheduler()`、`dl_task_check_affinity()`）；`add_nr_running()` 里的 `set_rd_overloaded()` 也改走 helper；文件数从 6 变 7（126 增 92 删）。**2/6–6/6 相对 v8 无实质变化**（6/6 的 diff 逐字相同）。
- 8/28 当日 v9 无人回帖。

## Maintainer 意见与讨论焦点

**Peter Zijlstra（v7 上，决定本系列形态）**：

> "This seems wrong; `rcu_dereference_protected()` is only supposed to be used during the update. And `rq->lock` is very much not the update side lock of the topology. Also, `&rq->__lock` is wrong. And this is far too verbose to endlessly repeat."

作者据此提出新宏并问 "Would you prefer `rcu_dereference_root_domain(p)`?"，Peter 的最终表态是接受但不热心：

> "Yeah, but I'm not sure I see the point of adding it, as it is exactly the same as `rcu_dereference_sched_domain()`. The root domains are part of the sched domains, so it doesn't seem wrong to me to use that existing one." … "*shrug*, either will do I suppose. You can create an alias if you think it helps."

即：**新增宏这个设计点仍有残留分歧**（Peter 认为复用 `rcu_dereference_sched_domain()` 就够，作者的理由是可读性与 grep 友好），但没有构成 NAK。

**Vincent Guittot**：只挑了 v7 里误删注释这一处。

**未解决/潜在问题**：作者自曝的 `dl_task_needs_bw_move()` 缺陷说明"哪些函数在什么锁下被调用"这件事，在 `root_domain` 读者集合上并没有权威清单。v9 补掉了已发现的三处，但判断依据是 Sashiko + 一次 virtme-ng 运行，不是穷举；`cpuset_mutex` 这条上下文（既非 `sched_domains_mutex` 也非 `rq->lock`）是否还有同类读者，线程里没人回答。

## 合入评估

**likelihood: possible**。

- 有利：改的是静态分析可见的正确性问题（Sparse/`CONFIG_PROVE_RCU`），不动调度决策语义；维护者给出的意见都已被采纳，且是"怎么选写法"层面的分歧而非方向性 NAK；迭代速度极快（v7→v9 一天半）。
- 卡点：`rcu_dereference_root_domain()` 这个新宏 Peter 只是"*shrug*"式放行，若他后续改口要求复用现有宏，还会再来一版；更实质的风险是 v9 是否穷尽了非法读者——作者自己已错过一次，任何一次新的 Sashiko/Lockdep 报告都会重置评审节奏。
- `next_action`：等 v9 的 review；若社区有 `!CONFIG_SMP` / `PREEMPT_RT` / 纯 `cpuset` 场景下的 `suspicious RCU usage` 复现，需要作者再迭代。

## 效果评估

无性能数据，也不需要——该系列不改变调度决策。可量化的只有静态分析结果：v9 作者给出的证据是一条 `WARNING: suspicious RCU usage`（`kernel/sched/deadline.c:3366`，`7.2.0-rc7-virtme-00041-g6509e33120f4`，virtme-ng 复现）以及 Sashiko 的静态检查报告；6/6 的 per-CPU debugfs 属于诊断可用性改进（离线 CPU 返回 `-ENODEV`），无测量数据。

## 我可以参与的点

- **帮忙穷举 `rq->rd` 的无锁读者**：这是本系列最缺的确定性输入。可以按 `->rd` 在 `kernel/sched/` 与 `kernel/cgroup/cpuset.c` 的交叉调用点上做一遍上下文归类（`rq->lock` / `sched_domains_mutex` / RCU 读侧 / 只持 `cpuset_mutex`），若发现 v9 漏掉的第四处，直接回帖就是有效 review。Sashiko 已经证明这条路径能出真问题。
- **在自己的机器上跑 `CONFIG_PROVE_RCU=y` + `CONFIG_DEBUG_ENTRY`/hotplug 循环**：CPU 上下线 + `cpuset` 分区变更 + SCHED_DEADLINE 任务设置的组合最容易踩到 `dl_*` 的 root_domain 读者，有 `suspicious RCU usage` 就值得回帖。
- **6/6 的 per-CPU debugfs 对生产排障有直接价值**：`/sys/kernel/debug/sched/cpu/cpu<N>/debug` 免去读整机 `/proc/sched_debug` 再切分，值得 Tested-by；如果内部内核的调度诊断工具链正在做单 CPU 视图，这个补丁的接口形态可以直接参考（也要注意到：近期站内已有讨论指出依赖 debugfs 的路径在 `CONFIG_DEBUG_FS=n` 时会静默失效）。
- **回合判断**：OLK-6.6 若开了 `CONFIG_PROVE_RCU`，v9 里被点名的几处（`set_rq_online/offline()`、`add_nr_running()`、`__sched_setscheduler()` 的 `rq->rd->span`/`dl_bw.bw`、`dl_task_check_affinity()`）是同一批可对照的读点；但 `__rcu` 标注 + helper 的完整回合依赖 7.x 的 `rcu_dereference_sched_domain()` 已存在，需要先在 6.6 里确认该宏。

## 参考链接

- v9 1/6: https://lore.kernel.org/all/20260827221809.988394-2-atomlin@atomlin.com/
- v9 6/6（per-CPU debugfs）: https://lore.kernel.org/all/20260827221809.988394-7-atomlin@atomlin.com/
- v8 1/6: https://lore.kernel.org/all/20260827194014.977758-2-atomlin@atomlin.com/
- v7 1/6: https://lore.kernel.org/all/20260826224238.936456-2-atomlin@atomlin.com/
- Peter Zijlstra 对 v7 的三条意见: https://lore.kernel.org/all/20260827073036.GC4121339@noisy.programming.kicks-ass.net/
- Peter Zijlstra 对新宏的 "*shrug*, either will do": https://lore.kernel.org/all/20260827105021.GJ687043@noisy.programming.kicks-ass.net/
- Vincent Guittot 的注释误删意见: https://lore.kernel.org/all/CAKfTPtACUPezTdiJKUW8zdb0NoURZU2Of+AnMU5VvzXE0tmB2g@mail.gmail.com/
- Sashiko 报告页（邮件原文给出）: https://sashiko.dev/#/patchset/20260827194014.977758-1-atomlin%40atomlin.com
- tip-bot commit: 未获取到
- stable backport: 未获取到

---
id: sched-20260828-005
date: '2026-08-28'
subject: "sched: Annotate rq->rd with __rcu and update lockless readers"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20260826224238.936456-2-atomlin@atomlin.com>"
lore_url: "https://lore.kernel.org/all/20260827221809.988394-2-atomlin@atomlin.com/"
authors: ["Aaron Tomlin"]
maintainers_involved: ["Peter Zijlstra", "Vincent Guittot"]
current_version: v9
patch_series:
  - version: v7
    msgid: "<20260826224238.936456-2-atomlin@atomlin.com>"
    date: '2026-08-27'
    summary: "逐点使用 rcu_dereference()/rcu_dereference_sched()/rcu_access_pointer() 保护 rq->rd 读者"
    review_outcome: "Peter Zijlstra 三条反对（protected 只用于更新侧、rq->lock 非拓扑更新锁、&rq->__lock 破坏抽象、过于啰嗦）；Vincent Guittot 指出误删注释"
  - version: v8
    msgid: "<20260827194014.977758-2-atomlin@atomlin.com>"
    date: '2026-08-28'
    summary: "引入 rcu_dereference_root_domain() 统一宏并全面替换读者"
    review_outcome: "作者当天自撤：Sashiko 查出 dl_task_needs_bw_move() 仅持 cpuset_mutex 的非法解引用，virtme-ng 复现 suspicious RCU usage"
  - version: v9
    msgid: "<20260827221809.988394-2-atomlin@atomlin.com>"
    date: '2026-08-28'
    summary: "dl_task_needs_bw_move() 套 guard(rcu)()；补 syscalls.c（__sched_setscheduler/dl_task_check_affinity）与 add_nr_running()；2/6-6/6 相对 v8 无实质变化"
    review_outcome: "当日无回帖"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - "Peter Zijlstra 对新增 rcu_dereference_root_domain() 仅以 *shrug* 放行，仍可能要求复用 rcu_dereference_sched_domain()"
    - "v9 是否穷尽 rq->rd 的非法无锁读者未被验证，作者已漏过一次"
    - "当日 v9 无任何 review 标签"
  next_action: "等 v9 review；作者/社区用 PROVE_RCU + Sashiko 再确认读者集合"
contribution_opportunities:
  - kind: review
    description: "按锁上下文穷举 rq->rd 读者（尤其 cpuset_mutex 一侧），确认 v9 是否仍有遗漏"
  - kind: testing
    description: "CONFIG_PROVE_RCU + CPU hotplug/cpuset 分区变更/DL 任务设置组合，回报 suspicious RCU usage"
  - kind: testing
    description: "测试 6/6 的 /sys/kernel/debug/sched/cpu/cpu<N>/debug 并给 Tested-by"
generated_at: "2026-09-07T22:08:24"
source_email_count: 14
related_articles: ["sched-20260827-001"]
tags: [sched_debug, topology, deadline, rt, cgroup]
---
