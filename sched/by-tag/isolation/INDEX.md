# tag: isolation

共 2 篇

- [sched-20261002-013](../../2026/10/sched-20261002-013-sched-isolation-enforce-nohz-full-as-a-subset-of-isolcpus-do.md) `feature/low/under_review` — Qiliang Yuan 的 12 补丁 v5（v1-v4 未在既往分析窗口覆盖；当日缓存收到的补丁为 01-03/12）：`kernel/sched/isolation.c` 的隔离语义修复与运行时可变 housekeeping 掩码。01/12 修 boot 配置矛盾——`nohz_full=`（或 `isolcpus=nohz`）与 `isolcpus=domain` 独立解析时，没有任何机
- [sched-20260803-013](../../2026/08/sched-20260803-013-sched-isolation-defer-freeing-of-bootmem-housekeeping-cpumasks-v2.md) `fix/low/under_review` — `sched/isolation` 推迟释放 bootmem housekeeping cpumask（08-02 系列 001）在 08-03 进入释放时机的讨论：应将释放推迟到 bootmem 回收阶段而非即刻 `memblock_free`。低严重度，合入可能性高。
