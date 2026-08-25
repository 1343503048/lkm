# tag: schedutil

共 5 篇

- [sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md](../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review`
- [sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md](../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review`
- [sched-20260823-009](../../2026/08/sched-20260823-009.md) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：cpufreq pressure 按「可达最高频率/当前可达最高频率」降 capacity，但 utilization 仅在频率不变架构才带匹配 scaling，导致语义不一致。焦点在「是否仅在不 invariant 场景施加 pressure」
- [sched-20260816-004](../../2026/08/sched-20260816-004-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/medium/merged_tip` — Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使
- [sched-20260807-003-schedutil-boost-dvfs-policy-max.md](../../2026/08/sched-20260807-003-schedutil-boost-dvfs-policy-max.md) `in-review`
