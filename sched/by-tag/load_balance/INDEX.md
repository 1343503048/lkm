# tag: load_balance

共 2 篇

- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260729-001](../../2026/07/sched-20260729-001-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。
