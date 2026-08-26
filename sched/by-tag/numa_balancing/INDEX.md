# tag: numa_balancing

共 3 篇

- [sched-20260807-020-sched-numa-hygon-remote-socket-distance.md](../../2026/08/sched-20260807-020-sched-numa-hygon-remote-socket-distance.md) `in-review`
- [sched-20260731-003](../../2026/07/sched-20260731-003-sched-topology-free-numa-masks-on-topology-allocation-failure.md) `fix/medium/under_review` — Fengyu Wang (Hygon) 修复 sched_init_numa() 中 topology 数组分配失败时的内存泄漏：masks 已发布但无法释放。补丁增加失败路径中的 masks 清理逻辑。带有 Fixes: 标签指向原始 commit cb83b629bae0。v1 刚发出，暂无 review 意见，合入可能性高。
- [sched-20260731-002](../../2026/07/sched-20260731-002-sched-fair-skip-numa-balancing-scan-on-memoryless-nodes.md) `bug/high/under_review` — Phineas Su (Google) 发现无内存 NUMA 节点上自动 NUMA balancing 导致 ~78% sys CPU 开销和持续 page fault 风暴。补丁在 task_tick_numa() 和 task_numa_work() 中增加 N_MEMORY 检查跳过扫描。但 PeterZ 和 Bharata 均不同意完全跳过扫描的方案，认为应在 mm 侧抑制迁移而非跳过整个
