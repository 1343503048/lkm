# tag: sched/fair

共 9 篇

- [sched-20260903-016](../../2026/09/sched-20260903-016.md) `patch_series/low/rfc` — `WF_SYNC` 是唤醒标志，用于表达「唤醒者即将睡眠、被唤醒者应立即在就近 CPU 运行」的放置意图。scx 调度类对该标志的放置语义此前缺乏明确文档。本系列（RFC）补上 `WF_SYNC` 在 scx 下的唤醒放置语义说明，帮助 BPF 调度器作者正确实现 `select_cpu` / `enqueue`。
- [sched-20260903-010](../../2026/09/sched-20260903-010.md) `patch_series/medium/under_review` — cpufreq 压力（`cpu.capacity` 因频率限制而下降）用于让调度器感知降频带来的算力损失。本系列延续 09-02 的 cpufreq pressure 讨论：仅在频率「不变（invariant）」的 CPU 上施加 cpufreq 压力，避免在频率本身随负载变化的平台上重复/错误地折算算力，导致任务放置与频率选择相互放大。
- [sched-20260903-009](../../2026/09/sched-20260903-009.md) `patch_series/medium/under_review` — `SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。
- [sched-20260903-002](../../2026/09/sched-20260903-002.md) `patch_series/medium/under_review` — steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。v12 相较 09-02 覆盖的 v11 主要做复审吸收与 rebase，并新增对虚拟化场景（paravirt / steal time 记账）的处理：对 vCPU 的 steal time 设上限，使宿主内核在 vCPU 被宿主机偷走时仍能判断「更空闲的 CPU」并迁移任务；同时引入 preferred CPU（结合 misfit / forced idle）以减少跨 LLC 抖动。
- [sched-20260903-001](../../2026/09/sched-20260903-001.md) `patch_series/medium/under_review` — 代理执行（proxy execution）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）分离。周期性 tick 中仍有部分记账/扫描以 donor 触发，导致 NUMA 周期扫描、`cache` 任务 tick、以及 workqueue 的 `wq_worker_tick()` 都基于「`sum_exec_runtime` 未被代理执行推进」的 donor 任务，造成 NUMA 扫描错位、cache tick 错配与 kworker 记账丢失。本系列把这几类周期行为改到基于 `rq->curr` 的真实执行上下文。
- [sched-20260902-014-steal-governor-v11-preferred-cpu](../../2026/09/sched-20260902-014-steal-governor-v11-preferred-cpu.md) `feature/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-25 的文章）
- [sched-20260902-010-sched-fair-update-curr-eevdf-root-cfs-rq-merged](../../2026/09/sched-20260902-010-sched-fair-update-curr-eevdf-root-cfs-rq-merged.md) `fix/low/merged_tip` — （本文为增量更新，完整背景见 related_articles 中 08-25/08-26 的文章）
- [sched-20260902-008-sched-fair-cpufreq-pressure-invariant](../../2026/09/sched-20260902-008-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）
- [sched-20260902-007-sched-fair-rework-task-h-load](../../2026/09/sched-20260902-007-sched-fair-rework-task-h-load.md) `fix/medium/under_review` — `task_h_load()` 用于负载均衡时估算任务在层级 cgroup 下的「层级负载」，其计算在