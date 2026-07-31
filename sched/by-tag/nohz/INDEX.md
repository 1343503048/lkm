# tag: nohz

共 3 篇

- [sched-20260730-008](../../2026/07/sched-20260730-008-sched-fair-prefer-fully-idle-cores-nohz-balancing-v2.md) `feature/under_review` — Andrea Righi 的 v2 补丁优化 NOHZ idle load balancer 的 CPU 选择：优先选择整个 SMT core 都 idle 的 CPU，避免唤醒部分空闲 core 的 sibling。在 NVIDIA Vera 的 GEMM 测试中从 6.2 TFLOP/s 提升到 9.4 TFLOP/s（+51%）。本文为增量更新，完整背景见 sched-20260729-00
- [sched-20260729-003](../../2026/07/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.md) `fix/high/under_review` — f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。
- [sched-20260729-001](../../2026/07/sched-20260729-001-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。
