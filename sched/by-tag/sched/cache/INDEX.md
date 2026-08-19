# tag: sched/cache

共 1 篇

- [sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains](../../2026/08/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.md) `fix/medium/under_review` — Sebastian Siewior 修复 `CONFIG_CPUSETS=n` 下读 `sched_rt_runtime_us` 因缺 `cpu_hotplug_lock` 触发的 backtrace，v2 把 `cpus_read_lock` 上移到 `rebuild_sched_domains()`。同时顺带修好 EAS 在 CPUfreq governor 切换时的同类问题。