# tag: idle


- [sched-20260804-003](../../2026/08/sched-20260804-003-sched-ext-fix-idle-cpu-state-init-v4-applied.md) `fix/medium/merged` — sched_ext 内置 idle 掩码初始化为 busy 的修复（08-03-002）在 08-04 发 v4，获 Kuba Piecuch Reviewed-by，并由 Tejun 以 tag `sched_ext-for-7.3` **合入**。这是 08-03-002 的收尾，状态更新为 merged。
- [sched-20260804-004](../../2026/08/sched-20260804-004-sched-ext-fixes-for-v7.2-rc6-pull.md) `fix/high/merged_tip` — Tejun 在 08-04 发出 sched_ext 的 7.2-rc6 fixes pull 第二波，延续 08-03-003 的稳定性修复集合（UAF / kernfs 死锁 / sync wakeup 误标 busy）。状态 merged_tip，等待 7.2-rc6 进入主线。这是 08-03-003 的延续。
- [sched-20260804-016](../../2026/08/sched-20260804-016-sched-psi-skip-cpus-zero-non-idle-delta.md) `feature/low/under_review` — PSI 统计中对非 idle 时间增量为 0 的 CPU 仍走完整更新路径，Dmitry Pletnev 改为跳过以减开销（大量 idle CPU 的系统受益明显）。低严重度优化，合入可能性 medium，需确认边界正确性。
- [sched-20260804-022](../../2026/08/sched-20260804-022-intel_idle-avoid-deep-idle-during-init.md) `fix/low/under_review` — intel_idle 在初始化/early 阶段若进入 deep idle 状态，可能在某些平台引起唤醒延迟异常或初始化时序问题。Zhang Rui 改为初始化期间避免 deep idle，完成后再允许。低严重度修复，合入可能性 medium，待平台确认。
- [sched-20260803-002](../../2026/08/sched-20260803-002-sched-ext-initialize-idle-masks-as-busy.md) `fix/medium/under_review` — sched_ext 内置 idle 掩码初始化时把全部 online CPU 误标为 idle，导致 busy CPU 被错误广播。改为保守地初始为空，待 bypass 解除后由真实 idle 转换填充。修复方向已获 Tejun 认可，合入概率高。
- [sched-20260803-003](../../2026/08/sched-20260803-003-sched-ext-fixes-for-v7.2-rc6.md) `fix/high/merged_tip` — Tejun 发出 sched_ext 的 7.2-rc6 fixes pull，修复子调度器生命周期中的多处 UAF / 死锁 / 错误状态，其中 sync wakeup 把 waker CPU 误标 idle 与 002 号文章（idle 掩码初始化）属同一正确性主题。已以 tag 提交，合入可能性=merged。
- [sched-20260801-009](../../2026/08/sched-20260801-009-cpufreq-intel-pstate-adjust-policy-cur-in-active-mode.md) `fix/low/under_review` — `intel_pstate` 在 performance policy 下把 CPU 钉到固定 pstate 后，却又把 `policy->cur` 覆写成 `policy->min`，导致 nohz_full 隔离 CPU 因为拿不到新的 APERF/MPERF 采样而**永远上报频率下限**。修复很直接：把 `policy->cur` 设为实际钉住的频率。Rafael 与 Srinivas 均
- [sched-20260801-005](../../2026/08/sched-20260801-005-sched-fair-prefer-fully-idle-cores-for-nohz-balancing-v3.md) `feature/under_review` — Andrea Righi 让 NOHZ idle load balancer 优先挑选整个 core 都空闲的 CPU，避免 ILB 跑在繁忙 SMT core 的空闲兄弟线程上而挤占其算力。方案本身简单合理、已经过三轮 reviewer 打磨，但**三个版本自始至终没有给出任何效果数据**，这是它目前唯一的明显短板。
- [sched-20260801-002](../../2026/08/sched-20260801-002-sched-ext-fix-idle-cpu-state-init-and-validation-v3.md) `fix/medium/under_review` — sched_ext 的 built-in idle mask 在初始化时把所有 online CPU 一律标记为 idle，但真正的 idle 跟踪要等调度器完全启用后才开始，导致 `ops.init()` 期间以及某些 CPU 下一次 idle 转换之前，繁忙 CPU 被错误地宣称为 idle。v3 把跟踪时机提前并顺带修掉了一个 selftest 的固有竞态，方案已按 review 意见收敛，
- [sched-20260730-003](../../2026/07/sched-20260730-003-sched-idle-sysbench-regression-f4c31b07b136.md) `bug/high/under_review` — Zhan Xusheng 报告 commit `f4c31b07b136`（sched/idle tick stop 相关）导致 sysbench threads 性能回退。Christian Loehle 和 Rafael J. Wysocki 讨论认为可能与 hypervisor 的 vCPU 调度交互有关，但目前信息不足以确定 root cause。Rafael 明确表示不会在完全理解问题之
- [sched-20260729-008](../../2026/07/sched-20260729-008-cpuidle-speed-up-do-idle-by-caching-the-governor-latency-qos.md) `feature/under_review` — Yaxiong Tian（麒麟）的 v2 系列把 cpuidle governor 的 latency QoS 约束聚合值按 CPU 缓存、经 QoS notifier 失效，将 cpuidle_governor_latency_req() 在 menu_select() 中的耗时占比从 19.9%（~1.9us/次）降到 4.2%（~0.3us/次）。idle 热路径优化方向合理，但暂无任何社区
- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260729-003](../../2026/07/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.md) `fix/high/under_review` — f4c31b07b136 让"无 cpuidle driver"路径也走 got_tick 启发式，导致 Oracle 在 OCI 小规格 VM 上 sysbench 回退最多 -29%；Christian Loehle（ARM）发出单行修复恢复无条件停 tick，Zhan Xusheng 同日给出机理分析。影响虚拟化场景明显，值得测试参与。
- [sched-20260728-010](../../2026/07/sched-20260728-010-sched-idle-sysbench-threads-regression-after-f4c31b07b136.md) `bug/high/under_review` — Oracle 性能测试发现 commit f4c31b07b136（"sched: idle: Consolidate the handling of two special cases"）导致 MySQL Sysbench threads 在 OCI VM 上出现 10%~29% 的性能回归。讨论持续近一个月，Rafael Wysocki 和 Christian Loehel 参与分析，目前根因
- [sched-20260726-007](../../2026/07/sched-20260726-007-selftests-sched-ext-make-allowed-cpus-idle-validation-race-free.md) `fix/medium/under_review` — 一组针对 sched_ext idle 跟踪与 selftest 竞态的修复：Kuba Piecuch 先修复 WAKE_SYNC 下 waker CPU 未被标记 busy 导致的 `allowed_cpus` selftest 偶发失败；Andrea Righi 跟进重写 selftest 的 idle 校验为无竞态版本。目标分支 `sched_ext/for-7.2-fixes`，合入可能性
- [sched-20260726-005](../../2026/07/sched-20260726-005-sched-ext-fix-incorrect-scx-pick-idle-cpu-flag-prefix-in-kernel-doc.md) `fix/low/merged_tip` — 一处 kernel-doc 文档 bug 修复：更正 `SCX_PICK_IDLE_CPU_*` 标志的前缀书写错误，已被 Tejun 直接应用到 `sched_ext/for-7.3`。琐碎文档修复，无需跟进。

## 文章
- [sched/fair: 让 is_core_idle() 检查核心内所有 CPU](../../2026/08/sched-20260807-015-sched-fair-is-core-idle-check-all-cpus.md)
- [sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新](../../2026/08/sched-20260807-019-sched-core-skip-avg-idle-no-idle-stamp.md)
- [sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新（v3）](../../2026/08/sched-20260808-001-sched-core-skip-avg-idle-v3.md)
- [kcov: 抑制定时器与调度器覆盖泄漏](../../2026/08/sched-20260808-002-kcov-scheduler-coverage-leaks.md)

共 4 篇
