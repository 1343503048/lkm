# tag: compatibility

共 6 篇

- [sched-20260824-006-sched-fair-null-deref-v4.19.md](../../2026/08/sched-20260824-006-sched-fair-null-deref-v4.19.md) `bug/high/under_review`
- [sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md](../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review`
- [sched-20260823-008](../../2026/08/sched-20260823-008.md) `fix/low/merged_tip` — `sched_ext Sync common/compat headers` 系列（08-19 009）的跟进回复：确认 `__scx_prolog_disables_migration` 默认值与「err high」注释不一致，在 cherry-pick 8e4f0b1ebcf2 的内核上 `is_migration_disabled(current)` 会少报。Changwoo 已在 scx 
- [sched-20260823-004](../../2026/08/sched-20260823-004.md) `fix/medium/under_review` — Dongli Zhang（Oracle）RFC：远程 CPU 更新 rq 时可能在 owner vCPU 仍被 host 抢占期间推进 rq->clock，导致 steal 间隔被错误计入。修复为抢占期间把 delta 累积到 `deferred_clock_task`，待 vCPU 重入时一并折回 irq/steal 记账。RFC 阶段，合入概率 medium。
- [sched-20260820-002](../../2026/08/sched-20260820-002.md) `feature/low/under_review` — Daniel T. Lee 把 sched_ext ops 的几个 container 指针参数（cs/cpuc/dsq/task 的 kptr）从 `PTR_UNTRUSTED` 改为 `PTR_TRUSTED`，因为 ops 调用上下文已保证其可信。用户写 BPF 调度器时不再被迫加冗余检查。已通过 bpf CI，合入概率高。
- [sched-20260819-009](../../2026/08/sched-20260819-009-sched-ext-sync-tools-headers-from-scx-repo.md) `fix/low/merged_tip` — Tejun 把 scx 仓库领先内核的工具头文件同步回内核树（`tools/sched_ext/include/scx`），修复 64 位 enum 恢复、v6.18+ `is_migration_disabled()` 少报等问题。已基于 `sched_ext/for-7.3-fixes`，属常规同步。
