# tag: numa_balancing

共 1 篇

- [sched-20260903-012](../../2026/09/sched-20260903-012.md) `patch_series/medium/rfc` — 作为 NUMA 细粒度均衡 + `sched/cache` 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。