# tag: topology


- [sched-20260806-002](../../2026/08/sched-20260806-002-sched-fair-nohz-fully-idle-core-v5.md) `feature/under_review` — NOHZ fully-idle-core v5（SMT core 选择）。延续 08-05-002。
- [sched-20260806-003](../../2026/08/sched-20260806-003-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review` — 简化 PREEMPT_DYNAMIC v2（Jinjie R-b）。延续 08-05-003。
- [sched-20260806-004](../../2026/08/sched-20260806-004-sched-core-dont-pin-idle-task-migrate-disable-switch.md) `fix/high/under_review` — sched/core 不要钉住 idle 任务（panic 修复）。
- [sched-20260806-009](../../2026/08/sched-20260806-009-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review` — sync wakeup core 粒度。延续 08-05-006。
- [sched-20260806-013](../../2026/08/sched-20260806-013-sched-fair-load-balance-identical-capacity-v6.md) `feature/under_review` — 相同 capacity CPU 间 LB v6。

- [sched-20260805-002](../../2026/08/sched-20260805-002-sched-fair-prefer-fully-idle-cores-nohz-v3-v4.md) `feature/under_review` — NOHZ fully-idle-core（SMT core 选择）。延续 08-04-005。
- [sched-20260805-003](../../2026/08/sched-20260805-003-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review` — 简化 PREEMPT_DYNAMIC（通用层）。延续 08-04-009。
- [sched-20260805-006](../../2026/08/sched-20260805-006-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review` — sync wakeup core 粒度。延续 08-04-006。
- [sched-20260805-007](../../2026/08/sched-20260805-007-sched-fair-wf_sync-semantics-wake-affine-doc.md) `feature/under_review` — WF_SYNC 语义 + 非 SMT 亲和。延续 08-04-006。
- [sched-20260805-008](../../2026/08/sched-20260805-008-sched-fair-decline-wf_sync-stacking-when-waker-llc-busier.md) `feature/under_review` — WF_SYNC 堆叠 LLC 忙闲判断。延续 08-04-006。
- [sched-20260805-009](../../2026/08/sched-20260805-009-sched-debug-per-cpu-debugfs-files.md) `feature/under_review` — per-CPU debugfs 文件。
- [sched-20260805-012](../../2026/08/sched-20260805-012-arm64-separate-preempt-resched-bits.md) `feature/under_review` — arm64 分离 resched 位 v4。延续 08-03-007。

- [sched-20260804-005](../../2026/08/sched-20260804-005-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.md) `feature/under_review` — NOHZ 负载均衡选 ilb（idle load balancer）CPU 时优先选「整核全 idle」的 CPU，避免把已运行兄弟线程的 SMT 核心当 ilb 损失吞吐。作者实测无调频噪声下 6.2→9.4 TFLOP/s，但加 ibs 噪声后提升消失。v3 已获 Vincent R-b，合入可能性高。
- [sched-20260804-006](../../2026/08/sched-20260804-006-sched-fair-sync-wakeups-target-waker-core.md) `discussion/under_review` — sync wakeup 优化在 08-04 呈三个并行子方向：选 waker 的 core、保留 wake-affine、非 SMT reciprocal 优先 waker cpu。延续 08-03-004 的「先定义统一 policy」要求，目前仍 medium，需先收敛策略再定补丁定位。
- [sched-20260804-010](../../2026/08/sched-20260804-010-sched-topology-restore-sd_prefer_sibling.md) `feature/under_review` — Chen Yu 在 EAS 路径上恢复 `SD_PREFER_SIBLING` 语义：当兄弟域是 MC 且非 cluster 时，倾向把任务集中到更少 CPU 以留出全 idle sibling 节能。v6 已获 Vincent R-b + Tested-by，合入可能性 high。
- [sched-20260804-011](../../2026/08/sched-20260804-011-sched-fair-allow-load-balance-identical-capacity.md) `feature/under_review` — `sched_balance_find_src_rq()` 的「~5% 额外容量」阈值无意中阻止了相同容量 CPU 间的迁移；Ricardo Neri 改为用 `get_actual_cpu_capacity()` 并经 `sched_cluster_active` 静态键保护，使 `CONFIG_SCHED_CLUSTER` 下能跨相同容量 cluster 均衡。v6 已两枚 Tested-by，合入可能性 high。
- [sched-20260804-012](../../2026/08/sched-20260804-012-sched-topology-free-numa-masks-on-alloc-failure.md) `fix/low/under_review` — `sched_domains_numa_masks` 在部分分配失败时未释放已分配掩码，存在错误路径泄漏。Hongling Zeng 补上清理。低严重度清理，属 medium（需确认与其它 topology 清理的合并）。
- [sched-20260803-004](../../2026/08/sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups.md) `discussion/under_review` — `sched/fair` 的「非 SMT reciprocal sync wakeup 优先选 waker CPU」补丁（v3）引发更深层的讨论：review 要求先定义 sync wakeup 的整体策略，而非零散修补。合入取决于策略共识，目前 medium。
- [sched-20260803-009](../../2026/08/sched-20260803-009-sched-numa-apply-remote-socket-distance-averaging-for-hygon-7447v.md) `feature/under_review` — `sched/numa` 针对 Hygon 7447V 的模块化布局，把远程 socket 节点距离取平均以区分 intra/inter-socket 远程代价。已获 Ingo Acked-by，合入可能性高。
- [sched-20260802-001](../../2026/08/sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks.md) `fix/low/under_review` — `housekeeping_init()` 在 deferred struct page 初始化完成之前调用 `memblock_free()` 释放 bootmem cpumask，在 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 时每种 housekeeping 类型触发一条 WARN 并给内核打上 `G W` 污点。补丁把释放动作推迟到 `core_initcal
- [sched-20260801-006](../../2026/08/sched-20260801-006-sched-cache-honor-migrate-llc-task-in-active-load-balance.md) `fix/medium/under_review` — cache-aware scheduling 的 `migrate_llc_task` 迁移类型在被动负载均衡切换到 active balance 的异步边界上丢失了，导致 CPU stopper 可能把任务搬到它 preferred LLC 之外。Lu Wang 用一个 rq 字段把迁移类型传递过去并补上目的 LLC 校验。修复思路清晰，但完全没有提供复现或效果证据。
- [sched-20260731-003](../../2026/07/sched-20260731-003-sched-topology-free-numa-masks-on-topology-allocation-failure.md) `fix/medium/under_review` — Fengyu Wang (Hygon) 修复 sched_init_numa() 中 topology 数组分配失败时的内存泄漏：masks 已发布但无法释放。补丁增加失败路径中的 masks 清理逻辑。带有 Fixes: 标签指向原始 commit cb83b629bae0。v1 刚发出，暂无 review 意见，合入可能性高。
- [sched-20260730-007](../../2026/07/sched-20260730-007-sched-isolation-defer-cpumask-memblock-freeing.md) `fix/medium/under_review` — Waiman Long 的 v4 补丁将 `house_mask` 的 memblock 内存释放延迟到 initcall 阶段，避免早期启动问题。Waiman 在 2026-07-30 ping 询问是否可合入，但暂无回复。
- [sched-20260730-005](../../2026/07/sched-20260730-005-sched-docs-document-cpu-preferred-mask.md) `feature/under_review` — Yury Norov 的 v9 文档系列（11 patches）为 `cpu_preferred_mask` 和 Preferred CPU 概念添加文档。社区讨论文档放置位置，可能移至 `sched-paravirt.rst`。
- [sched-20260728-006](../../2026/07/sched-20260728-006-sched-cache-fix-a-thread-aggregation-conflict-when-there-is.md) `fix/medium/under_review` — Zhan Xusheng 发出修复补丁，解决只有一个 runnable task 时的线程聚合冲突。Tim Chen (Intel) 已给出 Reviewed-by，并建议 `SD_ASYM_CPUCAPACITY` 相关代码保持现状。合入可能性高。

## 文章
- [cpufreq: CPPC 在热插拔/挂起恢复间保留 OSPM 设置的寄存器](../../2026/08/sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug.md)
- [sched/fair: 让 is_core_idle() 检查核心内所有 CPU](../../2026/08/sched-20260807-015-sched-fair-is-core-idle-check-all-cpus.md)
- [sched/numa: 为 Hygon model 7 应用远端 socket 距离平均](../../2026/08/sched-20260807-020-sched-numa-hygon-remote-socket-distance.md)
- [sched/fair: 非对称容量域负载均衡改进（已合入 tip/sched/core）](../../2026/08/sched-20260808-006-sched-fair-asym-capacity-load-balance-merged.md)

共 4 篇
