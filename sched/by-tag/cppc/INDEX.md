# tag: cppc

共 6 篇

- [sched-20261102-010](../../2026/11/sched-20261102-010-cpufreq-add-a-cpufreq-update-cpuinfo-policy-notifier-event.md) `feature/rfc` — Hugo Sales 的 RFC（4 patches，v1）：新增 `CPUFREQ_UPDATE_CPUINFO` policy notifier 事件，在 boost 开关等改变 `policy->cpuinfo.max_freq` 的时机通知依赖方（典型是 ACPI processor thermal 的节流步进，它按 `cpuinfo.max_freq` 的固定比例计算）。patch 2/
- [sched-20261031-004](../../2026/10/sched-20261031-004-acpi-cpufreq-cppc-add-ospm-nominal-perf-support.md) `feature/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261007-010](../../2026/10/sched-20261007-010-cpufreq-resolve-cppc-frequencies-to-performance-levels.md) `feature/low/under_review` — - sched-20260929-010：Christian Loehle 的 3 补丁系列——table-less 的 cppc-cpufreq 缺少「频率→性能级」解析，不同 kHz 请求 miss schedutil 频率缓存却写同一个 Desired Performance 值；新增 `->resolve_freq()` 回调、CPPC 预计算仿射转换、schedutil limits 未
- [sched-20261004-007](../../2026/10/sched-20261004-007-cpufreq-cppc-resolve-frequencies-to-performance-levels.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261002-005](../../2026/10/sched-20261002-005-cpufreq-resolve-cppc-frequencies-to-performance-levels.md) `feature/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20260804-021](../../2026/08/sched-20260804-021-cpufreq-cppc-resource-priority-sysfs.md) `feature/under_review` — CPPC v4（Resource Priority）新增 sysfs 接口，允许设置每个 CPU 的 CPPC 资源优先级，与 sched 的 uclamp/latency 偏好呼应，在共享电源域下影响硬件调度决策。v4 整合多轮反馈，合入可能性 medium（sysfs ABI 待确认）。
