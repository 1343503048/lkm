# tag: perf

共 5 篇

- [sched-20260729-008](../../2026/07/sched-20260729-008-cpuidle-speed-up-do-idle-by-caching-the-governor-latency-qos.md) `feature/under_review` — Yaxiong Tian（麒麟）的 v2 系列把 cpuidle governor 的 latency QoS 约束聚合值按 CPU 缓存、经 QoS notifier 失效，将 cpuidle_governor_latency_req() 在 menu_select() 中的耗时占比从 19.9%（~1.9us/次）降到 4.2%（~0.3us/次）。idle 热路径优化方向合理，但暂无任何社区
- [sched-20260729-007](../../2026/07/sched-20260729-007-perf-sched-latency-refine-outputs-unit-scaling-and-histogram.md) `feature/under_review` — Aaron Tomlin 的 perf sched latency 改进系列更新到 v4（07-26 的 v3 已收录为 sched-20260726-003，本篇为增量分析）：v4 集中解决 pipe mode 支持问题并加固 NULL 防护。工具类改动、迭代活跃、意见都被逐条回应，合入可能性高。
- [sched-20260729-005](../../2026/07/sched-20260729-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.md) `feature/under_review` — cache-aware 调度系列中的扫描开销优化（`task_cache_work()` 只扫 visited cpus）走到 v8，Tim Chen 给了 Reviewed-by；剩余讨论集中在一个罕见并发场景是否需要显式互斥，Chen Yu 判定可容忍、只需改注释。接近成熟。
- [sched-20260729-001](../../2026/07/sched-20260729-001-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NVIDIA 的 Andrea Righi 让 NOHZ idle load balancer 优先挑"整个物理核都空闲"的 CPU 来执行，避免 ILB 短暂唤醒 SMT 兄弟线程拖累另一个兄弟的单线程性能；GEMM 实测 6.2 → 9.4 TFLOP/s。当天讨论热烈（7 封），Peter Zijlstra 已介入，review 走向正面，值得关注 v2。
- [sched-20260726-003](../../2026/07/sched-20260726-003-perf-sched-latency-refine-outputs-unit-scaling-and-histogram-support.md) `feature/under_review` — Aaron Tomlin 改进 `perf sched latency` 的第 3 版：修复缺少 tracepoint 时误报成功的 bug、为延迟/运行时列做单位自适应缩放（ns/us/ms/s）、新增延迟直方图与时间区间过滤。属于 perf 工具侧的可用性增强，已迭代到 v3、逐条回应了 review，合入可能性较高。
