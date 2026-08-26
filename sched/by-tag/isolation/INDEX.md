# tag: isolation

共 1 篇

- [sched-20260803-013](../../2026/08/sched-20260803-013-sched-isolation-defer-freeing-of-bootmem-housekeeping-cpumasks-v2.md) `fix/low/under_review` — `sched/isolation` 推迟释放 bootmem housekeeping cpumask（08-02 系列 001）在 08-03 进入释放时机的讨论：应将释放推迟到 bootmem 回收阶段而非即刻 `memblock_free`。低严重度，合入可能性高。
