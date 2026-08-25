# tag: cpufreq

共 12 篇

- [sched-20260821-004](../../2026/08/sched-20260821-004-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `fix/medium/under_review` — cpufreq pressure 在非频率不变架构上会错误地降低 CPU capacity，导致利用率计算失衡。Wu Jianyong 的修复仅在 `arch_scale_freq_invariant()` 为真时应用 pressure，但 Vincent Guittot 质疑修复的必要性。
- [sched-20260816-004](../../2026/08/sched-20260816-004-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/medium/merged_tip` — Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使
- [sched-20260808-004-cpufreq-cppc-ospm-nominal-perf-v7.md](../../2026/08/sched-20260808-004-cpufreq-cppc-ospm-nominal-perf-v7.md) `in-review`
- [sched-20260807-005-cpufreq-cppc-highest-perf-update-limits.md](../../2026/08/sched-20260807-005-cpufreq-cppc-highest-perf-update-limits.md) `in-review`
- [sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug.md](../../2026/08/sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug.md) `in-review`
- [sched-20260807-003-schedutil-boost-dvfs-policy-max.md](../../2026/08/sched-20260807-003-schedutil-boost-dvfs-policy-max.md) `in-review`
- [sched-20260806-007](../../2026/08/sched-20260806-007-cpufreq-schedutil-fix-rate-limit-overflow-v3.md) `fix/high/under_review`
- [sched-20260806-006](../../2026/08/sched-20260806-006-sched-cpufreq-schedutil-boost-freq-handling.md) `fix/high/under_review`
- [sched-20260805-010](../../2026/08/sched-20260805-010-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/high/under_review`
- [sched-20260804-021](../../2026/08/sched-20260804-021-cpufreq-cppc-resource-priority-sysfs.md) `feature/under_review` — CPPC v4（Resource Priority）新增 sysfs 接口，允许设置每个 CPU 的 CPPC 资源优先级，与 sched 的 uclamp/latency 偏好呼应，在共享电源域下影响硬件调度决策。v4 整合多轮反馈，合入可能性 medium（sysfs ABI 待确认）。
- [sched-20260804-020](../../2026/08/sched-20260804-020-cpufreq-intel_pstate-consolidate-hwp-init.md) `cleanup/low/under_review` — Rafael 重构 intel_pstate 的 HWP P-state 初始化：引入 `intel_pstate_get_hwp_pstates()` 统一 HWP 专属初始化，移除冗余的 `intel_pstate_hybrid_hwp_adjust()` 及其 kerneldoc。声明无功能影响，低严重度清理，合入可能性 high。
- [sched-20260801-009](../../2026/08/sched-20260801-009-cpufreq-intel-pstate-adjust-policy-cur-in-active-mode.md) `fix/low/under_review` — `intel_pstate` 在 performance policy 下把 CPU 钉到固定 pstate 后，却又把 `policy->cur` 覆写成 `policy->min`，导致 nohz_full 隔离 CPU 因为拿不到新的 APERF/MPERF 采样而**永远上报频率下限**。修复很直接：把 `policy->cur` 设为实际钉住的频率。Rafael 与 Srinivas 均
