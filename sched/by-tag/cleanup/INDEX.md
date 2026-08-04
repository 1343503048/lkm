# tag: cleanup

共 2 篇

- [sched-20260804-008](../../2026/08/sched-20260804-008-sched-rt-minor-cleanups.md) `cleanup/low/under_review` — sched/rt 三笔小清理（删未用代码、修翻转注释、其它整洁化），声明无功能影响。低严重度清理，合入可能性 high。
- [sched-20260804-012](../../2026/08/sched-20260804-012-sched-topology-free-numa-masks-on-alloc-failure.md) `fix/low/under_review` — `sched_domains_numa_masks` 在部分分配失败时未释放已分配掩码，存在错误路径泄漏。Hongling Zeng 补上清理。低严重度清理，属 medium（需确认与其它 topology 清理的合并）。
