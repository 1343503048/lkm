---
layout: default
tag: "sched/fair"
title: "标签: sched/fair"
article_count: 35
---

- [sched-20260824-004](/lkm/2026/08/24/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.html) `discussion/low/under_review` — sched/fair: cpufreq pressure 频率不变性讨论（增量更新）
- [sched-20260824-006](/lkm/2026/08/24/sched-20260824-006-sched-fair-null-deref-v4.19.html) `bug/critical/under_review` — sched/fair: pick_next_task_fair NULL 解引用（v4.19 生产环境）
- [sched-20260824-011](/lkm/2026/08/24/sched-20260824-011-sched-fair-reuse-enqueue-delayed.html) `fix/none/under_review` — sched/fair: EEVDF 入队路径清理——复用 ENQUEUE_DELAYED 与避免重复计算
- [sched-20260823-002](/lkm/2026/08/23/sched-20260823-002.html) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fa...
- [sched-20260823-009](/lkm/2026/08/23/sched-20260823-009.html) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：...
- [sched-20260822-001](/lkm/2026/08/22/sched-20260822-001-sched-fair-use-update-curr-eevdf-for-remaining-root-cfs-rq-callers.html) `fix/low/under_review` — Zhan Xusheng 提出将 `update_curr_eevdf()` 统一应用于剩余的 root cfs_rq 调用路径
- [sched-20260821-004](/lkm/2026/08/21/sched-20260821-004-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.html) `fix/medium/under_review` — cpufreq pressure 在非频率不变架构上会错误地降低 CPU capacity
- [sched-20260820-001](/lkm/2026/08/20/sched-20260820-001.html) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时
- [sched-20260820-004](/lkm/2026/08/20/sched-20260820-004.html) `bug/low/under_review` — LKP sparse 在 `kernel/sched/fair.c:2004`（enqueue 路径判断 `cfs_rq->nr_running`）发出静...
- [sched-20260820-005](/lkm/2026/08/20/sched-20260820-005.html) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-...
- [sched-20260820-007](/lkm/2026/08/20/sched-20260820-007.html) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by
- [sched-20260820-009](/lkm/2026/08/20/sched-20260820-009.html) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」
- [sched-20260820-010](/lkm/2026/08/20/sched-20260820-010.html) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WAR...
- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group ...
- [sched-20260819-003](/lkm/2026/08/19/sched-20260819-003-sched-migrate-static-key-api-resend.html) `fix/low/under_review` — Hongyan Xia 把调度子系统里残留的 deprecated raw `static_key` API 统一迁移到新的 `static_branch...
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
- [sched-20260808-006-sched-fair-asym-capacity-load-balance-merged](/lkm/2026/08/08/sched-20260808-006-sched-fair-asym-capacity-load-balance-merged.html) `unknown/none/merged` — sched fair asym capacity load balance merged
- [sched-20260808-007-sched-fair-nohz-fully-idle-cores-merged](/lkm/2026/08/08/sched-20260808-007-sched-fair-nohz-fully-idle-cores-merged.html) `unknown/none/merged` — sched fair nohz fully idle cores merged
- [sched-20260807-015-sched-fair-is-core-idle-check-all-cpus](/lkm/2026/08/07/sched-20260807-015-sched-fair-is-core-idle-check-all-cpus.html) `unknown/none/in-review` — sched fair is core idle check all cpus
- [sched-20260807-016-sched-fair-nohz-fully-idle-cores](/lkm/2026/08/07/sched-20260807-016-sched-fair-nohz-fully-idle-cores.html) `unknown/none/in-review` — sched fair nohz fully idle cores
- [sched-20260807-017-sched-fair-wf-sync-stacking-decline](/lkm/2026/08/07/sched-20260807-017-sched-fair-wf-sync-stacking-decline.html) `unknown/none/in-review` — sched fair wf sync stacking decline
- [sched-20260807-018-sched-fair-wake-affine-nonsmt-reciprocal](/lkm/2026/08/07/sched-20260807-018-sched-fair-wake-affine-nonsmt-reciprocal.html) `unknown/none/in-review` — sched fair wake affine nonsmt reciprocal
- [sched-20260807-022-riscv-vector-preserve-state-scheduling](/lkm/2026/08/07/sched-20260807-022-riscv-vector-preserve-state-scheduling.html) `unknown/none/in-review` — riscv vector preserve state scheduling
