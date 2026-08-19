# tag: arch

共 2 篇

- [sched-20260804-009](../../2026/08/sched-20260804-009-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review` — 在 08-03-007 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` 的基础上，Mark Rutland 进一步简化 PREEMPT_DYNAMIC 的静态键选择与重写逻辑（6 笔 patch），收敛架构分支。这是 08-03-007 的延续，合入可能性 high。
- [sched-20260803-007](../../2026/08/sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits.md) `feature/under_review` — `preempt` 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，允许架构把 PREEMPT 与 NEED_RESCHED 位拆分存储，缓解 TIF 位紧张。Peter Zijlstra 要求合并前两 patch，s390 已给 Reviewed-by。合入可能性高。
