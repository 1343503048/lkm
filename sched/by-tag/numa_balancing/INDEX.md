# tag: numa_balancing

共 7 篇

- [sched-20260905-006](../../2026/09/sched-20260905-006-sched-numa-stop-vma-scan-filters-from-gating-promotion.md) `feature/medium/under_review` — task_numa_work() 在标记 VMA 以触发 hint fault 前会施加一系列 VMA 级过滤器。目前/2 新系列，本日收到复审（Re：80843 1/2、80869 2/2）。- 关注点：内存分层下 hint fault 作为提升机制，扫描过滤器不应成为提升的永久闸门。
- [sched-20260905-003](../../2026/09/sched-20260905-003-sched-core-make-fallback-cpu-selection-numa-aware.md) `discussion/medium/under_review` — select_fallback_rq() 先查本地节点，再按任务亲和性掩码的数值顺序扫描。目前作者 Yury Norov（NVIDIA），本日首次出现（新系列）。- 关注点：多 NUMA 节点下的 fallback 局部性。
- [sched-20260905-002](../../2026/09/sched-20260905-002-sched-debug-validate-writes-to-the-scan-size-mb-debugfs-knob.md) `fix/high/under_review` — scan_size_mb 在 task_scan_max() 中作为除数使用，而 debugfs_create_u32() 对写入值不做校验。目前v2 RESEND，作者重发以推进审阅。- 严重度 high：普通 debugfs 写入即可触发内核 panic，影响可测试性/稳定性。
- [sched-20260903-012](../../2026/09/sched-20260903-012-sched-cache-introduce-helpers-for-task-migration-decisions.md) `discussion/medium/rfc` — 作为 NUMA 细粒度均衡 + sched/cache 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。目前RFC v2 阶段，整体框架仍在讨论，尚未进入合入。- 与 sched-202
- [sched-20260807-020-sched-numa-hygon-remote-socket-distance.md](../../2026/08/sched-20260807-020-sched-numa-hygon-remote-socket-distance.md) `in-review`
- [sched-20260731-003](../../2026/07/sched-20260731-003-sched-topology-free-numa-masks-on-topology-allocation-failure.md) `fix/medium/under_review` — Fengyu Wang (Hygon) 修复 sched_init_numa() 中 topology 数组分配失败时的内存泄漏：masks 已发布但无法释放。补丁增加失败路径中的 masks 清理逻辑。带有 Fixes: 标签指向原始 commit cb83b629bae0。v1 刚发出，暂无 review 意见，合入可能性高。
- [sched-20260731-002](../../2026/07/sched-20260731-002-sched-fair-skip-numa-balancing-scan-on-memoryless-nodes.md) `bug/high/under_review` — Phineas Su (Google) 发现无内存 NUMA 节点上自动 NUMA balancing 导致 ~78% sys CPU 开销和持续 page fault 风暴。补丁在 task_tick_numa() 和 task_numa_work() 中增加 N_MEMORY 检查跳过扫描。但 PeterZ 和 Bharata 均不同意完全跳过扫描的方案，认为应在 mm 侧抑制迁移而非跳过整个
