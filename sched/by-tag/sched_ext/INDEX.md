# tag: sched_ext

共 3 篇

- [sched-20260902-006-sched-ext-null-deref-select-cpu-and](../../2026/09/sched-20260902-006-sched-ext-null-deref-select-cpu-and.md) `bug/high/under_review` — `sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
- [sched-20260902-005-sched-ext-vtime-ordering-v3](../../2026/09/sched-20260902-005-sched-ext-vtime-ordering-v3.md) `fix/low/under_review` — sched_ext 的 dsq（调度队列）按虚拟时间（vtime）排序，其中 `dsq_vtime` 依赖
- [sched-20260902-004-sched-ext-reject-nmi-lock-kfuncs](../../2026/09/sched-20260902-004-sched-ext-reject-nmi-lock-kfuncs.md) `fix/medium/under_review` — sched_ext 的若干 BPF kfunc 内部会获取锁（如 rq 锁、dsq 锁）。在 NMI 上下文调用这些