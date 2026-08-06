# tag: cpufreq

共 6 篇

- [sched-20260806-006](../../2026/08/sched-20260806-006-sched-cpufreq-schedutil-boost-freq-handling.md) `fix/high/under_review` — schedutil 对 boost 频率的 DVFS 请求修复（x86 Turbo / ARM）。
- [sched-20260806-007](../../2026/08/sched-20260806-007-cpufreq-schedutil-fix-rate-limit-overflow-v3.md) `fix/high/under_review` — schedutil rate_limit 溢出修复 v3（限幅只作用于写入、时间窗用原始目标）。延续 08-05-010。
- [sched-20260805-010](../../2026/08/sched-20260805-010-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/high/under_review` — schedutil 在频率限幅时 rate_limit 计算溢出，导致 last_freq_update_time 异常、调频抖动。Viresh 已确认 bug，建议优先 fix。

- [sched-20260804-020](../../2026/08/sched-20260804-020-cpufreq-intel_pstate-consolidate-hwp-init.md) `cleanup/low/under_review` — Rafael 重构 intel_pstate 的 HWP P-state 初始化：引入 `intel_pstate_get_hwp_pstates()` 统一 HWP 专属初始化，移除冗余的 `intel_pstate_hybrid_hwp_adjust()` 及其 kerneldoc。声明无功能影响，低严重度清理，合入可能性 high。
- [sched-20260804-021](../../2026/08/sched-20260804-021-cpufreq-cppc-resource-priority-sysfs.md) `feature/under_review` — CPPC v4（Resource Priority）新增 sysfs 接口，允许设置每个 CPU 的 CPPC 资源优先级，与 sched 的 uclamp/latency 偏好呼应，在共享电源域下影响硬件调度决策。v4 整合多轮反馈，合入可能性 medium（sysfs ABI 待确认）。
- [sched-20260801-009](../../2026/08/sched-20260801-009-cpufreq-intel-pstate-adjust-policy-cur-in-active-mode.md) `fix/low/under_review` — `intel_pstate` 在 performance policy 下把 CPU 钉到固定 pstate 后，却又把 `policy->cur` 覆写成 `policy->min`，导致 nohz_full 隔离 CPU 因为拿不到新的 APERF/MPERF 采样而**永远上报频率下限**。修复很直接：把 `policy->cur` 设为实际钉住的频率。Rafael 与 Srinivas 均
