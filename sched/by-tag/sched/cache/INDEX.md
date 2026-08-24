# tag: sched/cache

共 3 篇

- [sched-20260824-010-sched-cache-migrate-llc-active-lb](../../2026/08/sched-20260824-010-sched-cache-migrate-llc-active-lb.md) `fix/medium/under_review` — `migrate_llc_task` 提供了一种在 LLC 域内迁移任务的语义/提示。v3（Re: UID 54128）
- [sched-20260823-010](../../2026/08/sched-20260823-010.md) `fix/medium/under_review` — `sched/cache: honor migrate_llc_task semantics in active load balance` v3 已获 Tim Chen、Chen Yu 的 Reviewed-by，8/23 为 gentle ping 请 Peter 收下。核心是 active load balance 的迁移类型遵循 `migrate_llc_task` 语义，避免影响 delayed-dequeue 任务的 `migration_type` 含义。合入概率 high。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。