# tag: numa_balancing

共 4 篇

- [sched-20260905-006](../../2026/09/sched-20260905-006.md) `patch_series/medium/under_review` — `task_numa_work()` 在标记 VMA 以触发 hint fault 前会施加一系列 VMA 级过滤器。这些过滤器是当初 hint fault 作为「socket 驻留信号」时写的——跳过 VMA 只损失一些分辨率。但在内存分层（memory tiering）下，hint fault 不是信号而是机制：慢层 folio 之所以被考虑提升，正是因为扫描标记了它且随后被访问。被扫描排除的 VMA 会被永久排除在提升之外，因为过滤器输入来自扫描自身产生的 fault。
- [sched-20260905-003](../../2026/09/sched-20260905-003.md) `patch_series/medium/under_review` — `select_fallback_rq()` 先查本地节点，再按任务亲和性掩码的数值顺序扫描。在超过两个 NUMA 节点的系统上，可能选中比必要更远（跨更多 hop）的 CPU。本补丁改为遍历调度器的 NUMA hop 掩码，每次只考察新到达的 CPU，在整段 fallback 搜索中保持 locality；并在亲和性放宽后保持同样顺序。
- [sched-20260905-002](../../2026/09/sched-20260905-002.md) `fix/high/under_review` — `scan_size_mb` 在 `task_scan_max()` 中作为除数使用，而 `debugfs_create_u32()` 对写入值不做校验。向 `/sys/kernel/debug/sched/numa_balancing/scan_size_mb` 写入 0（或某些值）会在 `task_scan_max+0x30` 触发 "divide error" Oops，调用链 `init_numa_balancing → __sched_fork → sched_fork`，导致内核 panic。本补丁（v2 RESEND）对写入做合法性校验。
- [sched-20260903-012](../../2026/09/sched-20260903-012.md) `patch_series/medium/rfc` — 作为 NUMA 细粒度均衡 + `sched/cache` 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。