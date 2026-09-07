# tag: schedutil

共 6 篇

- [sched-20260904-005](../../2026/09/sched-20260904-005-cpufreq-schedutil-convert-to-kthread-create-worker.md) `discussion/low/under_review` — 将 cpufreq_schedutil（位于 kernel/sched/cpufreq_schedutil.c）从废弃的 kthread_run(kthread_worker_fn) 模式改用 kthread_create_worker()。目前作者 Bradley Morgan，v2 4/5。- 纯清理/modernization，无行为变更意图。
- [sched-20260903-010](../../2026/09/sched-20260903-010-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `discussion/medium/under_review` — cpufreq 压力（cpu.capacity 因频率限制而下降）用于让调度器感知降频带来的算力损失。目前本日为复审（Re）讨论，围绕 invariant 判定的边界与 schedutil 交互。
- [sched-20260902-008](../../2026/09/sched-20260902-008-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `fix/medium/under_review` — cpufreq pressure 只在频率不变的平台施加。补丁自 8 月进入评审以来仍未收口，9/2 是 Jianyong Wu 与 Hongyan Xia 就「概念到底该怎么表述」往返，没有新版本、没有新数据。
- [sched-20260823-009](../../2026/08/sched-20260823-009.md) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：cpufreq pressure 按「可达最高频率/当前可达最高频率」降 capacity，但 utilization 仅在频率不变架构才带匹配 scaling，导致语义不一致。焦点在「是否仅在不 invariant 场景施加 pressure」
- [sched-20260816-004](../../2026/08/sched-20260816-004-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/medium/merged_tip` — Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使
- [sched-20260807-003-schedutil-boost-dvfs-policy-max.md](../../2026/08/sched-20260807-003-schedutil-boost-dvfs-policy-max.md) `in-review`
