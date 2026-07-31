# tag: load_balance

共 4 篇

- [sched-20260730-008](../../2026/07/sched-20260730-008-sched-fair-prefer-fully-idle-cores-nohz-balancing-v2.md) `feature/under_review` — Andrea Righi 的 v2 补丁优化 NOHZ idle load balancer 的 CPU 选择：优先选择整个 SMT core 都 idle 的 CPU，避免唤醒部分空闲 core 的 sibling。在 NVIDIA Vera 的 GEMM 测试中从 6.2 TFLOP/s 提升到 9.4 TFLOP/s（+51%）。本文为增量更新，完整背景见 sched-20260729-00
- [sched-20260730-002](../../2026/07/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.md) `bug/high/under_review` — 0-Day robot 报告 `fb1050ac8e` 导致 netperf TCP_MAERTS 吞吐下降 14.6%。该 commit 将 cgroup-weight 计算从 smp 模式（flat）切换为 concur 模式（按 min(runnable, cpus) 缩放）。PeterZ 怀疑是 ksoftirqd 抢占行为变化导致，建议通过 slice 调优缓解。正在调查中。
- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260729-001](../../2026/07/sched-20260729-001-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。
