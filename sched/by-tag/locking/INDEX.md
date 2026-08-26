# tag: locking

共 4 篇

- [sched-20260821-009](../../2026/08/sched-20260821-009-futex-fix-might-sleep-warning-in-futex-pivot-pending.md) `fix/medium/merged_tip` — PeterZ 修复 `futex_pivot_pending()` 中的 `might_sleep()` 告警，已合入 `tip: locking/urgent` 分支。commit `d8aa5dd97944`。
- [sched-20260821-002](../../2026/08/sched-20260821-002-sched-allow-sleeping-spinlocks-on-preempt-rt-within-non-block.md) `fix/low/under_review` — PREEMPT_RT 下 non_block_start()/end() 区间内获取 sleeping spinlock 会触发 might_sleep() 告警。Sebastian 的修复为 `__might_resched()` 增加 `sleeping_lock` 参数区分正常调度与 sleeping lock 调度，David Woodhouse 已 ack。
- [sched-20260815-013](../../2026/08/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.md) `regression/high/under_review` — Martin King 报告并修复一个 RT 回归：`CONFIG_NO_RT_PUSH_IPI` 下，当 RT 任务 push 失败（找不到可运行的更低优先级 CPU）时，`rt_rq->rto` 计数未被扣除。残留的 rto 计数让后续 PI-boost 与任务迁移逻辑误判"有 overload"，导致饥饿/迁移停滞。严重度为 high。
- [sched-20260809-006](../../2026/08/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.md) `bug/high/under_review` — 2026-08-09 收到 3 封 KASAN use-after-free 报告（通过 iavf、dw_edma_pcie、bna 三种驱动触发），根因相同：mutex 乐观自旋读取 owner 任务的 `on_cpu` 字段时任务结构体已释放。属 high 严重度崩溃类 bug，尚无修复 patch。
