# tag: migration

共 2 篇

- [sched-20260918-020](../../2026/09/sched-20260918-020-sched-core-avoid-false-migration-warning-for-proxy-donors.md) `fix/low/merged_tip` — 增量更新：Andrea Righi 的 proxy execution 修复（避免对 migration-disabled 的被阻塞 donor 误报迁移告警）本日被 Peter Zijlstra 合入 tip 的 `sched/urgent` 分支（commit fe3c73d7bc76），Fixes b049b81bdff6，已获 John Stultz Acked-by。将随 sched/u
- [sched-20260822-002](../../2026/08/sched-20260822-002-sched-core-warn-on-is-migration-disabled-triggers.md) `bug/medium/under_review` — `sched/core: WARN_ON(is_migration_disabled())` 触发告警，表明任务在迁移被禁用时出现了意外的调度路径。需要调查触发条件。
