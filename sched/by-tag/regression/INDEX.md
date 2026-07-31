# tag: regression

共 4 篇

- [sched-20260730-003](../../2026/07/sched-20260730-003-sched-idle-sysbench-regression-f4c31b07b136.md) `bug/high/under_review` — Zhan Xusheng 报告 commit `f4c31b07b136`（sched/idle tick stop 相关）导致 sysbench threads 性能回退。Christian Loehle 和 Rafael J. Wysocki 讨论认为可能与 hypervisor 的 vCPU 调度交互有关，但目前信息不足以确定 root cause。Rafael 明确表示不会在完全理解问题之
- [sched-20260730-002](../../2026/07/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.md) `bug/high/under_review` — 0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。
- [sched-20260729-003](../../2026/07/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.md) `fix/high/under_review` — f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。
- [sched-20260728-010](../../2026/07/sched-20260728-010-sched-idle-sysbench-threads-regression-after-f4c31b07b136.md) `bug/high/under_review` — Oracle 性能测试发现 commit f4c31b07b136（"sched: idle: Consolidate the handling of two special cases"）导致 MySQL Sysbench threads 在 OCI VM 上出现 10%~29% 的性能回归。讨论持续近一个月，Rafael Wysocki 和 Christian Loehel 参与分析，目前根因
