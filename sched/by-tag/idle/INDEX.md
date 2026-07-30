# tag: idle

共 5 篇

- [sched-20260729-008](../../2026/07/sched-20260729-008-cpuidle-speed-up-do-idle-by-caching-the-governor-latency-qos.md) `feature/under_review` — Yaxiong Tian（麒麟）的 v2 系列把 cpuidle governor 的 latency QoS 约束聚合值按 CPU 缓存、经 QoS notifier 失效，将 cpuidle_governor_latency_req() 在 menu_select() 中的耗时占比从 19.9%（~1.9us/次）降到 4.2%（~0.3us/次）。idle 热路径优化方向合理，但暂无任何社区
- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260729-003](../../2026/07/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.md) `fix/high/under_review` — f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。
- [sched-20260726-007](../../2026/07/sched-20260726-007-selftests-sched-ext-make-allowed-cpus-idle-validation-race-free.md) `fix/medium/under_review` — 一组针对 sched_ext idle 跟踪与 selftest 竞态的修复：Kuba Piecuch 先修复 WAKE_SYNC 下 waker CPU 未被标记 busy 导致的 `allowed_cpus` selftest 偶发失败；Andrea Righi 跟进重写 selftest 的 idle 校验为无竞态版本。目标分支 `sched_ext/for-7.2-fixes`，合入可能性
- [sched-20260726-005](../../2026/07/sched-20260726-005-sched-ext-fix-incorrect-scx-pick-idle-cpu-flag-prefix-in-kernel-doc.md) `fix/low/merged_tip` — 一处 kernel-doc 文档 bug 修复：更正 `SCX_PICK_IDLE_CPU_*` 标志的前缀书写错误，已被 Tejun 直接应用到 `sched_ext/for-7.3`。琐碎文档修复，无需跟进。
