# tag: regression

共 2 篇

- [sched-20260729-003](../../2026/07/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.md) `fix/high/under_review` — f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。
- [sched-20260728-010](../../2026/07/sched-20260728-010-sched-idle-sysbench-threads-regression-after-f4c31b07b136.md) `bug/high/under_review` — Oracle 性能测试发现 commit f4c31b07b136（"sched: idle: Consolidate the handling of two special cases"）导致 MySQL Sysbench threads 在 OCI VM 上出现 10%~29% 的性能回归。讨论持续近一个月，Rafael Wysocki 和 Christian Loehel 参与分析，目前根因
