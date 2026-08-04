# tag: preempt

共 7 篇

- [sched-20260804-009](../../2026/08/sched-20260804-009-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review` — 在 08-03-007 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` 的基础上，Mark Rutland 进一步简化 PREEMPT_DYNAMIC 的静态键选择与重写逻辑（6 笔 patch），收敛架构分支。这是 08-03-007 的延续，合入可能性 high。
- [sched-20260804-018](../../2026/08/sched-20260804-018-rseq-fix-hard-lockup-granted-time-slice-extension-v3.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。
- [sched-20260803-007](../../2026/08/sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits.md) `feature/under_review` — `preempt` 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，允许架构把 PREEMPT 与 NEED_RESCHED 位拆分存储，缓解 TIF 位紧张。Peter Zijlstra 要求合并前两 patch，s390 已给 Reviewed-by。合入可能性高。
- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
- [sched-20260801-007](../../2026/08/sched-20260801-007-sched-preempt-count-cleanups-and-separate-resched-bits.md) `feature/under_review` — Boqun Feng 发出一个 24 patch 的 preempt_count 清理与重构系列，其中三个与调度核心直接相关：两个是 `kernel/sched/core.c` 中调试断言函数的参数与比较清理，一个是为 arm64 打开 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。改动本身低风险，但作为跨架构大系列，合入取决于整体协调。
- [sched-20260730-009](../../2026/07/sched-20260730-009-sched-dynamic-simplify-preempt-dynamic.md) `feature/under_review` — Mark Rutland 的 5-patch 系列简化 `PREEMPT_DYNAMIC` 配置。Mete Durlu 在 s390 上测试显示 vmlinux 减小约 1MB，bzImage 减小约 32KB，bloat-o-meter 显示净减少约 107KB。无行为变化报告。
