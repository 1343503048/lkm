# tag: arch

共 1 篇

- [sched-20260803-007](../../2026/08/sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits.md) `feature/under_review` — `preempt` 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，允许架构把 PREEMPT 与 NEED_RESCHED 位拆分存储，缓解 TIF 位紧张。Peter Zijlstra 要求合并前两 patch，s390 已给 Reviewed-by。合入可能性高。
