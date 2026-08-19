# tag: cleanup

共 3 篇

- [sched-20260816-003](../../2026/08/sched-20260816-003-sched-ext-move-the-config-off-sub-cap-kfunc-stubs-into-sub-c.md) `cleanup/low/merged_tip` — Tejun Heo 把 `CONFIG_EXT_SUB_SCHED` 关闭时 sub-cap kfunc 的 `EOPNOTSUPP` 桩函数从 `ext.c` 移到 `sub.c`，让所有 sub-scheduler kfunc 定义集中在同一文件（`sub.c`）。纯代码移动，无功能变化，已 apply 到 `sched_ext/for-7.3`。
- [sched-20260804-012](../../2026/08/sched-20260804-012-sched-topology-free-numa-masks-on-alloc-failure.md) `fix/low/under_review` — `sched_domains_numa_masks` 在部分分配失败时未释放已分配掩码，存在错误路径泄漏。Hongling Zeng 补上清理。低严重度清理，属 medium（需确认与其它 topology 清理的合并）。
- [sched-20260804-008](../../2026/08/sched-20260804-008-sched-rt-minor-cleanups.md) `cleanup/low/under_review` — sched/rt 三笔小清理（删未用代码、修翻转注释、其它整洁化），声明无功能影响。低严重度清理，合入可能性 high。
