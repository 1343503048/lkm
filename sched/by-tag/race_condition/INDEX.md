# tag: race_condition

共 2 篇

- [sched-20260821-006](../../2026/08/sched-20260821-006-sched-ext-serialize-concurrent-cpu-max-writers-in-scx-group-set-bandwidth.md) `fix/medium/under_review` — 并发写入同一 cgroup 的 cpu.max 会导致 SCX 侧的 `ops.cgroup_set_bandwidth()` 回调和 `tg->scx.bw_*` 缓存值交错，Changwoo Min 引入 `scx_cgroup_set_bw_mutex` 串行化 SCX 侧更新，作为 CFS `cfs_constraints_mutex` 的 SCX 对等物。
- [sched-20260821-001](../../2026/08/sched-20260821-001-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx-divergence.md) `fix/medium/under_review` — 并发写入 cgroup 控制文件（如 cpu.shares/cpu.weight）会导致 CFS 与 SCX 之间的状态不一致。v2 方案将 CFS 锁提升到 core 层，让 CFS 和 SCX 回调在同一把锁下原子执行，PeterZ 已认可方向。
