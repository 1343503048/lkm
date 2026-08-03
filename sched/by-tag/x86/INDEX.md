# tag: x86

共 3 篇

- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
- [sched-20260802-001](../../2026/08/sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks.md) `fix/low/under_review` — `housekeeping_init()` 在 deferred struct page 初始化完成之前调用 `memblock_free()` 释放 bootmem cpumask，在 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 时每种 housekeeping 类型触发一条 WARN 并给内核打上 `G W` 污点。补丁把释放动作推迟到 `core_initcal
- [sched-20260726-006](../../2026/07/sched-20260726-006-sched-update-the-thread-info-in-task-description.md) `fix/low/stalled` — Huacai Chen 更新 `THREAD_INFO_IN_TASK` 的 Kconfig 描述，纠正一处过时且误导的说明（并非要删除除 flags 外的所有字段，实际只需移除 task_struct 指针字段）。补丁自 6/9 发出后一直无人 review，7/26 作者发出 "Gentle ping?" 催促，目前停滞。
