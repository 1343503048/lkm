# tag: topology

共 8 篇

- [sched-20260803-004](../../2026/08/sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups.md) `discussion/under_review` — `sched/fair` 的「非 SMT reciprocal sync wakeup 优先选 waker CPU」补丁（v3）引发更深层的讨论：review 要求先定义 sync wakeup 的整体策略，而非零散修补。合入取决于策略共识，目前 medium。
- [sched-20260803-009](../../2026/08/sched-20260803-009-sched-numa-apply-remote-socket-distance-averaging-for-hygon-7447v.md) `feature/under_review` — `sched/numa` 针对 Hygon 7447V 的模块化布局，把远程 socket 节点距离取平均以区分 intra/inter-socket 远程代价。已获 Ingo Acked-by，合入可能性高。
- [sched-20260802-001](../../2026/08/sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks.md) `fix/low/under_review` — `housekeeping_init()` 在 deferred struct page 初始化完成之前调用 `memblock_free()` 释放 bootmem cpumask，在 `CONFIG_DEFERRED_STRUCT_PAGE_INIT=y` 时每种 housekeeping 类型触发一条 WARN 并给内核打上 `G W` 污点。补丁把释放动作推迟到 `core_initcal
- [sched-20260801-006](../../2026/08/sched-20260801-006-sched-cache-honor-migrate-llc-task-in-active-load-balance.md) `fix/medium/under_review` — cache-aware scheduling 的 `migrate_llc_task` 迁移类型在被动负载均衡切换到 active balance 的异步边界上丢失了，导致 CPU stopper 可能把任务搬到它 preferred LLC 之外。Lu Wang 用一个 rq 字段把迁移类型传递过去并补上目的 LLC 校验。修复思路清晰，但完全没有提供复现或效果证据。
- [sched-20260731-003](../../2026/07/sched-20260731-003-sched-topology-free-numa-masks-on-topology-allocation-failure.md) `fix/medium/under_review` — Fengyu Wang (Hygon) 修复 sched_init_numa() 中 topology 数组分配失败时的内存泄漏：masks 已发布但无法释放。补丁增加失败路径中的 masks 清理逻辑。带有 Fixes: 标签指向原始 commit cb83b629bae0。v1 刚发出，暂无 review 意见，合入可能性高。
- [sched-20260730-007](../../2026/07/sched-20260730-007-sched-isolation-defer-cpumask-memblock-freeing.md) `fix/medium/under_review` — Waiman Long 的 v4 补丁将 `house_mask` 的 memblock 内存释放延迟到 initcall 阶段，避免早期启动问题。Waiman 在 2026-07-30 ping 询问是否可合入，但暂无回复。
- [sched-20260730-005](../../2026/07/sched-20260730-005-sched-docs-document-cpu-preferred-mask.md) `feature/under_review` — Yury Norov 的 v9 文档系列（11 patches）为 `cpu_preferred_mask` 和 Preferred CPU 概念添加文档。社区讨论文档放置位置，可能移至 `sched-paravirt.rst`。
- [sched-20260728-006](../../2026/07/sched-20260728-006-sched-cache-fix-a-thread-aggregation-conflict-when-there-is.md) `fix/medium/under_review` — Zhan Xusheng 发出修复补丁，解决只有一个 runnable task 时的线程聚合冲突。Tim Chen (Intel) 已给出 Reviewed-by，并建议 `SD_ASYM_CPUCAPACITY` 相关代码保持现状。合入可能性高。
