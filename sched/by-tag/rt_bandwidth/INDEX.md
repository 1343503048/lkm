# tag: rt_bandwidth

共 5 篇

- [sched-20261107-011](../../2026/11/sched-20261107-011-sched-remove-config-rt-group-sched.md) `discussion/rfc` — 本文为增量更新，完整脉络见下。
- [sched-20261106-009](../../2026/11/sched-20261106-009-sched-remove-config-rt-group-sched.md) `discussion/rfc` — Sebastian Andrzej Siewior 提议删除 `CONFIG_RT_GROUP_SCHED`（-1438 行）：它「broken beyond repair」，启用后无法给任务设 SCHED_FIFO/RR（cgroup 无 runtime 可分配、cgroup v2 根本不能分配 runtime）、SCHED_DEADLINE 准入也卡死，主流发行版（Debian/OpenSus
- [sched-20261017-004](../../2026/10/sched-20261017-004-sched-rt-queue-a-push-when-a-queued-rt-task-is-boosted.md) `fix/high/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261015-001](../../2026/10/sched-20261015-001-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.md) `regression/high/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20260924-001](../../2026/09/sched-20260924-001-sched-rt-rebuild-domains-only-after-successful-rt-sysctl-wri.md) `fix/medium/under_review` — Joseph Salisbury 的修复补丁：把 `rebuild_sched_domains()` 从「每次 RT sysctl 写入前无条件执行」改为「仅当写入成功且值真实变化时」才执行，消除 RT 周期/运行时间参数每次读取都触发全量调度域重建的开销。本日 Chengfeng Lin 给出独立实测：在 v7.2 上该补丁把 RT sysctl 读延迟从约 8.57us 降到 0.264us（
