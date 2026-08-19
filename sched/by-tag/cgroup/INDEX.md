# tag: cgroup

共 13 篇

- [sched-20260818-005](../../2026/08/sched-20260818-005-sched-flatten-the-pick-v3-benchmarks.md) `feature/medium/under_review` — Szabina 在 s390 LPAR（32 vCPU）上对 "Flatten the pick" v3 系列做了详细 benchmark（schbench、sysbench、hackbench），含 stress-ng 并行负载。关键发现：无并行负载时结果普遍正面（高线程数最高 -9.55%），但 stress-ng 并行时低线程数场景出现回退（最高 +2.36%），且 stress-ng 自身
- [sched-20260818-004](../../2026/08/sched-20260818-004-sched-ext-allow-ops-cgroup-set-bandwidth-to-be-sleepable.md) `feature/medium/under_review` — Changwoo Min 提交单 patch 将 `ops.cgroup_set_bandwidth()` 加入 sched_ext cgroup 操作的 sleepable 白名单，使 BPF 调度器在 cgroup 获得 cpu.max 限制时可按需分配内存，而非预保留。Tejun Heo review 要求加 `__retain`、统一 marker 前缀并集中放置。
- [sched-20260817-003](../../2026/08/sched-20260817-003.md) `feature/high/merged_tip` — Ingo Molnar 发出 v7.3 合并窗口的 **Scheduler updates for v7.3** PR，规模巨大：flatten-the-pick cgroup 调度（扁平权重、运行在 per-CPU 队列而非 cgroup 层级）、EEVDF 核心拆解到单 run queue（CFS 去掉每 cgroup 内部队列）、short-slice 延迟优化、RT 抢占下限、scx 的 
- [sched-20260815-014](../../2026/08/sched-20260815-014.md) `fix/low/merged_tip` — Vincent Guittot 的 EEVDF cgroup 权重修复由 tip-bot 合入 `sched/core`：把子权重"扁平化"，使 CPU 时间按权重比例分配，而非被层级结构过度约束。属于 08-14 系列 001（EEVDF/cgroup 权重扁平化）的延续/定稿。
- [sched-20260814-008](../../2026/08/sched-20260814-008.md) `feature/under_review` — Ziyang Men 提交 v1（2 patches）「cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats」。为 cgroup CPU 控制器提供高效 BPF 读取统计（CFS 带宽计数直接读字段，新增 kfunc 计算 throttled time）。含 selftest。under_review。
- [sched-20260807-013-sched-preserve-reset-on-fork.md](../../2026/08/sched-20260807-013-sched-preserve-reset-on-fork.md) `in-review`
- [sched-20260807-002-sched-ext-find-parent-sched-null-check.md](../../2026/08/sched-20260807-002-sched-ext-find-parent-sched-null-check.md) `in-review`
- [sched-20260805-004](../../2026/08/sched-20260805-004-sched-fair-remove-dead-throttled-check-pick-task-fair.md) `cleanup/low/superseded`
- [sched-20260804-004](../../2026/08/sched-20260804-004-sched-ext-fixes-for-v7.2-rc6-pull.md) `fix/high/merged_tip` — Tejun 在 08-04 发出 sched_ext 的 7.2-rc6 fixes pull 第二波，延续 08-03-003 的稳定性修复集合（UAF / kernfs 死锁 / sync wakeup 误标 busy）。状态 merged_tip，等待 7.2-rc6 进入主线。这是 08-03-003 的延续。
- [sched-20260803-003](../../2026/08/sched-20260803-003-sched-ext-fixes-for-v7.2-rc6.md) `fix/high/merged_tip` — Tejun 发出 sched_ext 的 7.2-rc6 fixes pull，修复子调度器生命周期中的多处 UAF / 死锁 / 错误状态，其中 sync wakeup 把 waker CPU 误标 idle 与 002 号文章（idle 掩码初始化）属同一正确性主题。已以 tag 提交，合入可能性=merged。
- [sched-20260801-001](../../2026/08/sched-20260801-001-sched-ext-bandwidth-limited-rescue-execution.md) `feature/under_review` — Tejun Heo 发出 12 个 patch 的系列，为 sched_ext 层级调度（子调度器）补上一条内核兜底路径：当子调度器持有的 cid 无法覆盖某个任务的亲和性时，内核以受限带宽直接把该任务跑起来，而不是让它在 cap 拒绝与重新入队之间反复直到调度器被驱逐或任务 stall。这是 sched_ext 层级化能力的关键补齐，由子系统 maintainer 本人提出，值得关注。
- [sched-20260730-002](../../2026/07/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.md) `bug/high/under_review` — 0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
