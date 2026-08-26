# tag: sched/cache

共 8 篇

- [sched-20260823-010](../../../2026/08/sched-20260823-010.md) `fix/medium/under_review` — `sched/cache: honor migrate_llc_task semantics in active load balance` v3 已获 Tim Chen、Chen Yu 的 Reviewed-by，8/23 为 gentle ping 请 Peter 收下。核心是 active load balance 的迁移类型遵循 `migrate_llc_task` 语义，避免影响 del
- [sched-20260820-005](../../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。
- [sched-20260819-005](../../../2026/08/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.md) `fix/medium/under_review` — Sebastian Siewior 修复 `CONFIG_CPUSETS=n` 下读 `sched_rt_runtime_us` 因缺 `cpu_hotplug_lock` 触发的 backtrace，v2 把 `cpus_read_lock` 上移到 `rebuild_sched_domains()`。同时顺带修好 EAS 在 CPUfreq governor 切换时的同类问题。
- [sched-20260815-007](../../../2026/08/sched-20260815-007-sched-ext-scx-flatcg-expire-cached-hweights-on-weight-cha-2.md) `feature/low/under_review` — 本系列（接 08-14 002 的 scx_flatcg 权重连续性讨论）继续推进：当 cgroup 层级权重变更时，让 `scx_flatcg` 缓存的 hweights 失效并重算，避免 stale 权重被沿用。Tao Cui 提方案，Tejun 已有替代思路但未定稿。
- [sched-20260815-006](../../../2026/08/sched-20260815-006-sched-ext-scx-flatcg-expire-cached-hweights-on-weight-change.md) `fix/low/merged_tip` — Tao Cui 的 `cvtime` true-up 补丁：修复 `scx_pair`/`scx_flatcg` 中 cvtime（消费虚拟时间）钳制与 hweight（层级权重）不一致的问题——consume 时给 cvtime 增加下限钳制。已 apply 到 sched_ext（Tejun 称后续会做更大重构）。
- [sched-20260810-010](../../../2026/08/sched-20260810-010-sched-cache-fix-a-thread-aggregation-conflict-when-there-is-.md) `fix/low/under_review` — Chen Yu 提交 v2「sched/cache: Fix a thread aggregation conflict when there is one runnable task」。修复 active load balance 在 LLC 内仅有一个可运行任务时的错误聚合/搬移。under_review。
- [sched-20260809-002](../../../2026/08/sched-20260809-002-sched-cache-honor-migrate-llc-task-semantics-in-active-load-.md) `fix/low/under_review` — Lu Wang 提交 v2，让 active load balance 尊重 `migrate_llc_task` 的缓存感知迁移语义，避免把被标记 prefer-LLC 的任务不必要地跨 LLC 搬移。处于 under_review。
- [sched-20260807-010-sched-cache-active-lb-migrate-llc-task.md](../../../2026/08/sched-20260807-010-sched-cache-active-lb-migrate-llc-task.md) `in-review`
