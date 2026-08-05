# tag: cgroup

共 6 篇

- [sched-20260805-004](../../2026/08/sched-20260805-004-sched-fair-remove-dead-throttled-check-pick-task-fair.md) `cleanup/merged` — pick_task_fair 删除失效 throttled 检查（CFS 带宽控制相关）。已合入 85570f10a4c6。

- [sched-20260804-004](../../2026/08/sched-20260804-004-sched-ext-fixes-for-v7.2-rc6-pull.md) `fix/high/merged_tip` — Tejun 在 08-04 发出 sched_ext 的 7.2-rc6 fixes pull 第二波，延续 08-03-003 的稳定性修复集合（UAF / kernfs 死锁 / sync wakeup 误标 busy）。状态 merged_tip，等待 7.2-rc6 进入主线。这是 08-03-003 的延续。
- [sched-20260803-003](../../2026/08/sched-20260803-003-sched-ext-fixes-for-v7.2-rc6.md) `fix/high/merged_tip` — Tejun 发出 sched_ext 的 7.2-rc6 fixes pull，修复子调度器生命周期中的多处 UAF / 死锁 / 错误状态，其中 sync wakeup 把 waker CPU 误标 idle 与 002 号文章（idle 掩码初始化）属同一正确性主题。已以 tag 提交，合入可能性=merged。
- [sched-20260801-001](../../2026/08/sched-20260801-001-sched-ext-bandwidth-limited-rescue-execution.md) `feature/under_review` — Tejun Heo 发出 12 个 patch 的系列，为 sched_ext 层级调度（子调度器）补上一条内核兜底路径：当子调度器持有的 cid 无法覆盖某个任务的亲和性时，内核以受限带宽直接把该任务跑起来，而不是让它在 cap 拒绝与重新入队之间反复直到调度器被驱逐或任务 stall。这是 sched_ext 层级化能力的关键补齐，由子系统 maintainer 本人提出，值得关注。
- [sched-20260730-002](../../2026/07/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.md) `bug/high/under_review` — 0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
