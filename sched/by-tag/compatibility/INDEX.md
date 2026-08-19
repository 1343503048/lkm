# tag: compatibility

共 1 篇

- [sched-20260819-009-sched-ext-sync-tools-headers-from-scx-repo](../../2026/08/sched-20260819-009-sched-ext-sync-tools-headers-from-scx-repo.md) `fix/low/merged_tip` — Tejun 把 scx 仓库领先内核的工具头文件同步回内核树（`tools/sched_ext/include/scx`），修复 64 位 enum 恢复、v6.18+ `is_migration_disabled()` 少报等问题。已基于 `sched_ext/for-7.3-fixes`，属常规同步。