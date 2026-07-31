# tag: topology

共 3 篇

- [sched-20260730-007](../../2026/07/sched-20260730-007-sched-isolation-defer-cpumask-memblock-freeing.md) `fix/medium/under_review` — Waiman Long 的 v4 补丁将 `house_mask` 的 memblock 内存释放延迟到 initcall 阶段，避免早期启动问题。Waiman 在 2026-07-30 ping 询问是否可合入，但暂无回复。
- [sched-20260730-005](../../2026/07/sched-20260730-005-sched-docs-document-cpu-preferred-mask.md) `feature/under_review` — Yury Norov 的 v9 文档系列（11 patches）为 `cpu_preferred_mask` 和 Preferred CPU 概念添加文档。社区讨论文档放置位置，可能移至 `sched-paravirt.rst`。
- [sched-20260728-006](../../2026/07/sched-20260728-006-sched-cache-fix-a-thread-aggregation-conflict-when-there-is.md) `fix/medium/under_review` — Zhan Xusheng 发出修复补丁，解决只有一个 runnable task 时的线程聚合冲突。Tim Chen (Intel) 已给出 Reviewed-by，并建议 `SD_ASYM_CPUCAPACITY` 相关代码保持现状。合入可能性高。
