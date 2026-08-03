# tag: cgroup

共 3 篇

- [sched-20260801-001](../../2026/08/sched-20260801-001-sched-ext-bandwidth-limited-rescue-execution.md) `feature/under_review` — Tejun Heo 发出 12 个 patch 的系列，为 sched_ext 层级调度（子调度器）补上一条内核兜底路径：当子调度器持有的 cid 无法覆盖某个任务的亲和性时，内核以受限带宽直接把该任务跑起来，而不是让它在 cap 拒绝与重新入队之间反复直到调度器被驱逐或任务 stall。这是 sched_ext 层级化能力的关键补齐，由子系统 maintainer 本人提出，值得关注。
- [sched-20260730-002](../../2026/07/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.md) `bug/high/under_review` — 0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
