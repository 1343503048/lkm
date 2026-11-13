# tag: rt_bandwidth

共 11 篇

- [sched-20261113-010](../../2026/11/sched-20261113-010-sched-rt-throttling-cleanup-and-a-bit-of-documentation.md) `feature/under_review` — 本文为增量更新，完整脉络见下。
- [sched-20261112-010](../../2026/11/sched-20261112-010-sched-rt-throttling-cleanup-and-a-bit-of-documentation.md) `feature/under_review` — 本文为增量更新，完整脉络见下。
- [sched-20261111-001](../../2026/11/sched-20261111-001-sched-rt-throttling-cleanup-and-a-bit-of-documentation.md) `feature/under_review` — Sebastian Andrzej Siewior（PREEMPT_RT 维护者）发 v2 七补丁系列，梳理 RT throttling 机制遗留的历史包袱：把 CONFIG_RT_GROUP_SCHED 标记为 broken（作者想直接删除但未被允许）、把 SCHED_DEADLINE 的准入控制从 `sched_rt_{period,runtime}_us` 解耦并迁到 `/sys/kerne
- [sched-20261110-007](../../2026/11/sched-20261110-007-hierarchical-constant-bandwidth-server.md) `feature/rfc` — Yuri Andriaccio 发第 7 版 RFC（29 补丁），用层次化 Constant Bandwidth Server（HCBS）替换现有 `RT_GROUP_SCHED` 机制，为 rt-cgroup 提供理论上更稳健、且与 SCHED_DEADLINE/SCHED_EXT 一致的带宽隔离。v7 相对 v6 变化巨大：rebase 到 7.4-rc1、修掉 v6 评审与 sashiko
- [sched-20261109-012](../../2026/11/sched-20261109-012-bug-sched-rt-rlimit-rttime-not-reset-after-blocking-under.md) `bug/medium/under_review` — 社区报告一个 RT 调度 bug：任务从 SCHED_FIFO 切到 SCHED_OTHER 并阻塞睡眠后，RLIMIT_RTTIME 的 RT 运行时间计数器没有复位——反复「FIFO 跑 8ms → 切 SCHED_OTHER → 睡眠 10ms」会让 RT runtime 跨睡眠累计，最终触发 SIGXCPU，即便每次 RT 执行区间都低于限制。附完整 reproducer，Ubuntu 7
- [sched-20261109-001](../../2026/11/sched-20261109-001-sched-deadline-bandwidth-accounting-fixes-and-selftests.md) `fix/high/under_review` — 本文为增量更新，完整脉络见下。
- [sched-20261107-011](../../2026/11/sched-20261107-011-sched-remove-config-rt-group-sched.md) `discussion/rfc` — 本文为增量更新，完整脉络见下。
- [sched-20261106-009](../../2026/11/sched-20261106-009-sched-remove-config-rt-group-sched.md) `discussion/rfc` — Sebastian Andrzej Siewior 提议删除 `CONFIG_RT_GROUP_SCHED`（-1438 行）：它「broken beyond repair」，启用后无法给任务设 SCHED_FIFO/RR（cgroup 无 runtime 可分配、cgroup v2 根本不能分配 runtime）、SCHED_DEADLINE 准入也卡死，主流发行版（Debian/OpenSus
- [sched-20261017-004](../../2026/10/sched-20261017-004-sched-rt-queue-a-push-when-a-queued-rt-task-is-boosted.md) `fix/high/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261015-001](../../2026/10/sched-20261015-001-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.md) `regression/high/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20260924-001](../../2026/09/sched-20260924-001-sched-rt-rebuild-domains-only-after-successful-rt-sysctl-wri.md) `fix/medium/under_review` — Joseph Salisbury 的修复补丁：把 `rebuild_sched_domains()` 从「每次 RT sysctl 写入前无条件执行」改为「仅当写入成功且值真实变化时」才执行，消除 RT 周期/运行时间参数每次读取都触发全量调度域重建的开销。本日 Chengfeng Lin 给出独立实测：在 v7.2 上该补丁把 RT sysctl 读延迟从约 8.57us 降到 0.264us（
