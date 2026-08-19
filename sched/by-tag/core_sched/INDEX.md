# tag: core_sched

共 11 篇

- [sched-20260817-003](../../2026/08/sched-20260817-003.md) `feature/high/merged_tip` — Ingo Molnar 发出 v7.3 合并窗口的 **Scheduler updates for v7.3** PR，规模巨大：flatten-the-pick cgroup 调度（扁平权重、运行在 per-CPU 队列而非 cgroup 层级）、EEVDF 核心拆解到单 run queue（CFS 去掉每 cgroup 内部队列）、short-slice 延迟优化、RT 抢占下限、scx 的 
- [sched-20260816-002](../../2026/08/sched-20260816-002.md) `fix/medium/merged_tip` — Tejun Heo 的 4-patch 系列修正在 `sched_ext` core-sched 任务排序的实现：修复 `ops.core_sched_before()` 被倒置调用的 bug（`Fixes: 7b0888b7cc19`，stable v6.12+）、用 `p->scx.runnable_at` 统一等待追踪、让跨两个调度器的任务对按最近公共祖先排序、删除 dequeue 路径里已
- [sched-20260815-012](../../2026/08/sched-20260815-012.md) `feature/low/under_review` — Tejun Heo 让 `ops.sub_ecaps_updated()` 回调期间处于 dispatch 上下文，使 sub-scheduler 在能力和权重更新时能直接调用 `scx_bpf_dispatch*()` 等 dispatch 类 kfunc。已规划 follow-up 重构（删 rbtn / 层级权重）。v1 刚发出。
- [sched-20260810-006](../../2026/08/sched-20260810-006.md) `fix/medium/under_review` — Tejun Heo 提交 6-patch core-sched 稳定性系列（core-sched flips 等待在途选择、pick_task() 释放 rq 锁的竞态处理）。Peter 在 PATCH 1/6、2/6 给出详细反馈。under_review。
- [sched-20260809-003](../../2026/08/sched-20260809-003.md) `discussion/low/under_review` — Mete Durlu 在 2026-08-09 对前一天（08-08）提交的 `is_core_idle()` 修改 patch 发起讨论/追问，延续该系列。属 discussion，尚无定论。
- [sched-20260808-003-sched-ext-core-scheduling-fixes.md](../../2026/08/sched-20260808-003-sched-ext-core-scheduling-fixes.md) `in-review`
- [sched-20260807-001-proxy-execution-sleeping-owner-v31.md](../../2026/08/sched-20260807-001-proxy-execution-sleeping-owner-v31.md) `in-review`
- [sched-20260806-011](../../2026/08/sched-20260806-011-sched-wake_q-stable-6.12y-helper.md) `fix/low/under_review`
- [sched-20260806-010](../../2026/08/sched-20260806-010-sched-ext-proxy-execution-conservative-terminate.md) `feature/under_review`
- [sched-20260805-001](../../2026/08/sched-20260805-001-sched-ext-proxy-exec-reject-dsq-class-transition.md) `feature/under_review`
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
