# tag: capacity

共 2 篇

- [sched-20260804-017](../../2026/08/sched-20260804-017-sched-docs-document-cpu_preferred_mask.md) `feature/under_review` — Shrikanth Hegde 把 `cpu_preferred_mask`（per-task 偏好的大/小核子集，用于节能与缓存热）概念文档化，作为 cpu_preferred_mask 系列（v9→v10）的一部分。作者公开表示仍在等待一组 benchmark 数字支撑合入。合入可能性 medium——明确等数据。
- [sched-20260804-011](../../2026/08/sched-20260804-011-sched-fair-allow-load-balance-identical-capacity.md) `feature/under_review` — `sched_balance_find_src_rq()` 的「~5% 额外容量」阈值无意中阻止了相同容量 CPU 间的迁移；Ricardo Neri 改为用 `get_actual_cpu_capacity()` 并经 `sched_cluster_active` 静态键保护，使 `CONFIG_SCHED_CLUSTER` 下能跨相同容量 cluster 均衡。v6 已两枚 Tested-by
