# tag: crash

共 9 篇

- [sched-20260815-009](../../2026/08/sched-20260815-009-sched-ext-fix-exit-task-leak-on-fork-failure-during-enable.md) `fix/medium/merged_tip` — Tejun Heo 的补丁：当 `fork()` 失败时正确释放 `scx_task_state`，避免每进程 sched_ext 状态泄漏。已 apply 到 sched_ext。与 005/008 同属"任务退出/创建失败生命周期"健壮性议题。
- [sched-20260815-008](../../2026/08/sched-20260815-008-sched-ext-don-t-rehome-a-dead-task-in-scx-cgroup-task-migrat.md) `fix/medium/stale` — Tao Cui 的"不要对已 gone 的任务做 rehome"补丁，在 `scx_kick_bpf` 路径检测任务已进入 gone 状态则跳过 rehome。Tejun 指出该问题已由 `ops.exit_task` 处理，Tao 同意 withdraw。属被 superseded/withdrawn 的提案。
- [sched-20260815-005](../../2026/08/sched-20260815-005-sched-ext-dispatch-path-follow-ups.md) `fix/medium/under_review` — Tao Cui 的 v2 patch：当目标 DSQ 已被 `scx_task_exit()` 销毁时，`scx_dispatch()`/consume 不再 `BUG_ON` 直接 panic，而是立即返回。避免任务退出竞态触发的内核崩溃。与 009 系列（exit_task 资源泄漏）同根因、互补。
- [sched-20260810-005](../../2026/08/sched-20260810-005-perf-core-fix-group-leader-use-after-free-after-sibling-deta.md) `fix/high/merged_tip` — Aditya Chillara 的 perf 事件组 leader use-after-free 修复已由 tip-bot 合入 `tip/perf/urgent`（2026-08-10 报告），属紧急高严重度崩溃修复。无需额外 review。
- [sched-20260810-003](../../2026/08/sched-20260810-003-sched-debug-validate-writes-to-the-scan-size-mb-debugfs-knob.md) `fix/high/under_review` — Zhan Xusheng 提交 v2「sched/debug: Validate writes to scan_size_mb」。该值被写成 0 会在 NUMA 平衡扫描逻辑中触发 divide error panic（由 Chen Yu 指出）。v2 增加写入校验与 sysctl 文档。属 high 严重度崩溃修复，合入可能性高。
- [sched-20260809-006](../../2026/08/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.md) `bug/high/under_review` — 2026-08-09 收到 3 封 KASAN use-after-free 报告（通过 iavf、dw_edma_pcie、bna 三种驱动触发），根因相同：mutex 乐观自旋读取 owner 任务的 `on_cpu` 字段时任务结构体已释放。属 high 严重度崩溃类 bug，尚无修复 patch。
- [sched-20260807-021-selftests-sched-ext-exit-skeleton-open.md](../../2026/08/sched-20260807-021-selftests-sched-ext-exit-skeleton-open.md) `in-review`
- [sched-20260807-009-perf-core-group-leader-use-after-free.md](../../2026/08/sched-20260807-009-perf-core-group-leader-use-after-free.md) `in-review`
- [sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx.md](../../2026/08/sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx.md) `in-review`
