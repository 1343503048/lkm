# tag: schedutil

共 6 篇

- [sched-20260904-005](../../2026/09/sched-20260904-005-cpufreq-schedutil-convert-to-kthread-create-worker.md) `discussion/low/under_review` — 把 `kernel/sched/cpufreq_schedutil.c` 里 `sugov_policy` 的 kthread worker 从已废弃的 `kthread_init_worker()` + `kthread_create(kthread_worker_fn, ...)` + `wake_up_process()` 组合换成 `kthread_create_worker()` / `
- [sched-20260903-010](../../2026/09/sched-20260903-010-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `discussion/medium/under_review` — `get_actual_cpu_capacity()` 无条件从容量里扣掉 `max(hw_load_avg, cpufreq_get_pressure())`，但只有频率不变（`arch_scale_freq_invariant()` 为真）的架构上 util 才会随频率同比例缩放；在没有频率不变性的机器上，满载 CPU 无论跑多高频率都会累计到完整 `SCHED_CAPACITY_SCALE`
- [sched-20260902-008](../../2026/09/sched-20260902-008-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `fix/medium/under_review` — Jianyong Wu（Hygon）的单补丁：只在 `arch_scale_freq_invariant()` 为真时才把 cpufreq pressure 计入 `get_actual_cpu_capacity()`。9/2 这天的实质结论是**作者承认标题里的因果口径错了**——他对 Hongyan Xia 说 "I will re-phrase the problem statement i
- [sched-20260823-009](../../2026/08/sched-20260823-009.md) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：cpufreq pressure 按「可达最高频率/当前可达最高频率」降 capacity，但 utilization 仅在频率不变架构才带匹配 scaling，导致语义不一致。焦点在「是否仅在不 invariant 场景施加 pressure」
- [sched-20260816-004](../../2026/08/sched-20260816-004-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/medium/merged_tip` — Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使
- [sched-20260807-003-schedutil-boost-dvfs-policy-max.md](../../2026/08/sched-20260807-003-schedutil-boost-dvfs-policy-max.md) `in-review`
