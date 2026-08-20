---
layout: default
tag: "sched/fair"
title: "标签: sched/fair"
article_count: 22
---

- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — 配套修复补丁 tg_cpus() 在 cpuset 为空时返回 0，使 shares_max 归零绕过 MIN_SHARES 下限，导致 group se 的 ...
- [sched-20260819-003](/lkm/2026/08/19/sched-20260819-003-sched-migrate-static-key-api-resend.html) `fix/low/under_review` — 将调度子系统中直接使用的 raw static_key / static_key_{true,false}() 及 __cfs_bandwidth_used、p...
- [sched-20260818-005](/lkm/2026/08/18/sched-20260818-005-sched-flatten-the-pick-v3-benchmarks.html) `feature/medium/under_review` — sched: Flatten the pick — v3 s390 benchmark results
- [sched-20260817-004](/lkm/2026/08/17/sched-20260817-004-sched-urgent-for-v7-2.html) `fix/medium/merged_tip` — sched/urgent for v7.2
- [sched-20260817-005](/lkm/2026/08/17/sched-20260817-005-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.html) `feature/medium/under_review` — sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff
- [sched-20260815-014](/lkm/2026/08/15/sched-20260815-014-sched-fair-fix-flat-hierarchy.html) `fix/low/merged_tip` — sched/fair: Fix flat hierarchy
- [sched-20260814-001](/lkm/2026/08/14/sched-20260814-001-sched-fair-fix-flat-hierarchy.html) `fix/medium/merged_tip` — sched/fair: Fix flat hierarchy
- [sched-20260810-002](/lkm/2026/08/10/sched-20260810-002-sched-fair-use-list-for-each-entry-rcu-in-print-cfs-stats.html) `fix/medium/under_review` — sched/fair: Use list_for_each_entry_rcu() in print_cfs_stats()
- [sched-20260810-009](/lkm/2026/08/10/sched-20260810-009-sched-ext-move-reject-dsq-draining-into-core.html) `feature/none/under_review` — sched_ext: Move reject DSQ draining into core
- [sched-20260810-010](/lkm/2026/08/10/sched-20260810-010-sched-cache-fix-a-thread-aggregation-conflict-when-there-is-.html) `fix/low/under_review` — sched/cache: Fix a thread aggregation conflict when there is one runnable task
- [sched-20260810-012](/lkm/2026/08/10/sched-20260810-012-sched-fair-let-sync-wakeups-target-the-waker-s-core.html) `feature/none/under_review` — sched/fair: Let sync wakeups target the waker's core
- [sched-20260810-014](/lkm/2026/08/10/sched-20260810-014-sched-fair-drop-min-vruntime-call-from-set-protect-slice.html) `discussion/low/under_review` — sched/fair: Drop min_vruntime() call from set_protect_slice()
- [sched-20260809-001](/lkm/2026/08/09/sched-20260809-001-sched-debug-introduce-per-cpu-debugfs-files.html) `feature/none/under_review` — sched/debug: Introduce per-CPU debugfs files
- [sched-20260809-002](/lkm/2026/08/09/sched-20260809-002-sched-cache-honor-migrate-llc-task-semantics-in-active-load-.html) `fix/low/under_review` — sched cache honor migrate llc task semantics in active load 
- [sched-20260809-003](/lkm/2026/08/09/sched-20260809-003-sched-fair-make-is-core-idle-check-all-cpus-in-a-core.html) `discussion/low/under_review` — sched/fair: Make is_core_idle() check all cpus in a core
- [sched-20260808-006-sched-fair-asym-capacity-load-balance-merged](/lkm/2026/08/08/sched-20260808-006-sched-fair-asym-capacity-load-balance-merged.html) `unknown/none/merged` — sched/fair: 非对称容量域负载均衡改进（已合入 tip/sched/core）
- [sched-20260808-007-sched-fair-nohz-fully-idle-cores-merged](/lkm/2026/08/08/sched-20260808-007-sched-fair-nohz-fully-idle-cores-merged.html) `unknown/none/merged` — sched/fair: NOHZ 负载均衡优先选择完全空闲核心（已合入 tip）
- [sched-20260807-015-sched-fair-is-core-idle-check-all-cpus](/lkm/2026/08/07/sched-20260807-015-sched-fair-is-core-idle-check-all-cpus.html) `unknown/none/in-review` — sched/fair: 让 is_core_idle() 检查核心内所有 CPU
- [sched-20260807-016-sched-fair-nohz-fully-idle-cores](/lkm/2026/08/07/sched-20260807-016-sched-fair-nohz-fully-idle-cores.html) `unknown/none/in-review` — sched/fair: NOHZ 负载均衡优先选择完全空闲核心
- [sched-20260807-017-sched-fair-wf-sync-stacking-decline](/lkm/2026/08/07/sched-20260807-017-sched-fair-wf-sync-stacking-decline.html) `unknown/none/in-review` — sched/fair: 当 waker 的 LLC 是瓶颈时拒绝 WF_SYNC 堆叠
- [sched-20260807-018-sched-fair-wake-affine-nonsmt-reciprocal](/lkm/2026/08/07/sched-20260807-018-sched-fair-wake-affine-nonsmt-reciprocal.html) `unknown/none/in-review` — sched/fair: 在非 SMT 互逆关系下保留 wake-affine CPU
- [sched-20260807-022-riscv-vector-preserve-state-scheduling](/lkm/2026/08/07/sched-20260807-022-riscv-vector-preserve-state-scheduling.html) `unknown/none/in-review` — riscv: 在非零 Vector 嵌套深度调度时保留 Vector 状态
