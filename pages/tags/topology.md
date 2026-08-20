---
layout: default
tag: "topology"
title: "标签: topology"
article_count: 32
---

- [sched-20260819-005](/lkm/2026/08/19/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.html) `fix/medium/under_review` — 读 /proc/sys/kernel/sched_rt_runtime_us 在 CONFIG_CPUSETS=n 下因缺少 cpu_hotplug_lock ...
- [sched-20260814-003](/lkm/2026/08/14/sched-20260814-003-sched-topology-add-a-cpus-read-lock-to-rebuild-sched-domains.html) `fix/medium/under_review` — sched/topology: Add a cpus_read_lock to rebuild_sched_domains()
- [sched-20260810-013](/lkm/2026/08/10/sched-20260810-013-sched-topology-don-t-claim-sched-domain-shared-twice-on-the-.html) `fix/low/under_review` — sched/topology: don't claim sched_domain_shared twice on the same domain
- [sched-20260808-006-sched-fair-asym-capacity-load-balance-merged](/lkm/2026/08/08/sched-20260808-006-sched-fair-asym-capacity-load-balance-merged.html) `unknown/none/merged` — sched/fair: 非对称容量域负载均衡改进（已合入 tip/sched/core）
- [sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug](/lkm/2026/08/07/sched-20260807-004-cpufreq-cppc-preserve-registers-hotplug.html) `unknown/none/in-review` — cpufreq: CPPC 在热插拔/挂起恢复间保留 OSPM 设置的寄存器
- [sched-20260807-015-sched-fair-is-core-idle-check-all-cpus](/lkm/2026/08/07/sched-20260807-015-sched-fair-is-core-idle-check-all-cpus.html) `unknown/none/in-review` — sched/fair: 让 is_core_idle() 检查核心内所有 CPU
- [sched-20260807-020-sched-numa-hygon-remote-socket-distance](/lkm/2026/08/07/sched-20260807-020-sched-numa-hygon-remote-socket-distance.html) `unknown/none/in-review` — sched/numa: 为 Hygon model 7 应用远端 socket 距离平均
- [sched-20260806-002](/lkm/2026/08/06/sched-20260806-002-sched-fair-nohz-fully-idle-core-v5.html) `feature/none/under_review` — sched/fair: Prefer fully idle cores for NOHZ balancing
- [sched-20260806-003](/lkm/2026/08/06/sched-20260806-003-sched-dynamic-simplify-preempt_dynamic-v2.html) `feature/none/under_review` — sched: dynamic: Simplify preempt_schedule{,_notrace}()
- [sched-20260806-004](/lkm/2026/08/06/sched-20260806-004-sched-core-dont-pin-idle-task-migrate-disable-switch.html) `fix/high/under_review` — sched/core: Don't pin the idle task in migrate_disable_switch()
- [sched-20260806-009](/lkm/2026/08/06/sched-20260806-009-sched-fair-sync-wakeup-target-waker-core.html) `feature/none/under_review` — sched/fair: Let sync wakeups target the waker's core
- [sched-20260806-013](/lkm/2026/08/06/sched-20260806-013-sched-fair-load-balance-identical-capacity-v6.html) `feature/none/under_review` — sched/fair: Allow load balancing between CPUs of identical capacity
- [sched-20260805-002](/lkm/2026/08/05/sched-20260805-002-sched-fair-prefer-fully-idle-cores-nohz-v3-v4.html) `feature/none/under_review` — sched/fair: Prefer fully idle cores for NOHZ balancing
- [sched-20260805-003](/lkm/2026/08/05/sched-20260805-003-sched-dynamic-simplify-preempt_dynamic-v2.html) `feature/none/under_review` — sched dynamic simplify preempt_dynamic v2
- [sched-20260805-006](/lkm/2026/08/05/sched-20260805-006-sched-fair-sync-wakeup-target-waker-core.html) `feature/none/under_review` — sched/fair: Let sync wakeups target the waker's core
- [sched-20260805-007](/lkm/2026/08/05/sched-20260805-007-sched-fair-wf_sync-semantics-wake-affine-doc.html) `feature/none/under_review` — sched/fair: Let sync wakeups target the waker's core
- [sched-20260805-008](/lkm/2026/08/05/sched-20260805-008-sched-fair-decline-wf_sync-stacking-when-waker-llc-busier.html) `feature/none/under_review` — sched/fair: decline WF_SYNC stacking when waker LLC is the busier share
- [sched-20260805-009](/lkm/2026/08/05/sched-20260805-009-sched-debug-per-cpu-debugfs-files.html) `feature/medium/under_review` — sched debug per cpu debugfs files
- [sched-20260805-012](/lkm/2026/08/05/sched-20260805-012-arm64-separate-preempt-resched-bits.html) `feature/none/under_review` — arm64: sched/preempt: Enable HAS_SEPARATE_PREEMPT_RESCHED_BITS
- [sched-20260804-005](/lkm/2026/08/04/sched-20260804-005-sched-fair-prefer-fully-idle-cores-for-nohz-balancing.html) `feature/none/under_review` — sched/fair: Allow load balancing between CPUs of identical capacity
- [sched-20260804-006](/lkm/2026/08/04/sched-20260804-006-sched-fair-sync-wakeups-target-waker-core.html) `discussion/none/under_review` — sched/fair: Let sync wakeups target the waker's core
- [sched-20260804-010](/lkm/2026/08/04/sched-20260804-010-sched-topology-restore-sd_prefer_sibling.html) `feature/none/under_review` — sched/topology: Restore SD_PREFER_SIBLING in domains with asymmetric capacity
- [sched-20260804-011](/lkm/2026/08/04/sched-20260804-011-sched-fair-allow-load-balance-identical-capacity.html) `feature/none/under_review` — sched/fair: Allow load balancing between CPUs of identical capacity
- [sched-20260804-012](/lkm/2026/08/04/sched-20260804-012-sched-topology-free-numa-masks-on-alloc-failure.html) `fix/low/under_review` — sched/numa: Fix scan period for remote private faults
- [sched-20260803-004](/lkm/2026/08/03/sched-20260803-004-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wakeups.html) `discussion/none/under_review` — sched fair prefer waker cpu for non smt reciprocal sync wakeups
- [sched-20260803-009](/lkm/2026/08/03/sched-20260803-009-sched-numa-apply-remote-socket-distance-averaging-for-hygon-7447v.html) `feature/none/under_review` — sched/numa: Apply remote socket distance averaging for Hygon 7447V
- [sched-20260802-001](/lkm/2026/08/02/sched-20260802-001-sched-isolation-defer-freeing-of-the-bootmem-housekeeping-cpumasks.html) `fix/low/under_review` — sched/isolation: Defer freeing of the bootmem housekeeping cpumasks
- [sched-20260801-006](/lkm/2026/08/01/sched-20260801-006-sched-cache-honor-migrate-llc-task-in-active-load-balance.html) `fix/medium/under_review` — sched cache honor migrate llc task in active load balance
- [sched-20260731-003](/lkm/2026/07/31/sched-20260731-003-sched-topology-free-numa-masks-on-topology-allocation-failure.html) `fix/medium/under_review` — sched/topology: Free NUMA masks on topology allocation failure
- [sched-20260730-005](/lkm/2026/07/30/sched-20260730-005-sched-docs-document-cpu-preferred-mask.html) `feature/none/under_review` — sched/docs: Document cpu_preferred_mask and Preferred CPU concept
- [sched-20260730-007](/lkm/2026/07/30/sched-20260730-007-sched-isolation-defer-cpumask-memblock-freeing.html) `fix/medium/under_review` — sched/isolation: Defer freeing of cpumask memblock memory to initcall
- [sched-20260728-006](/lkm/2026/07/28/sched-20260728-006-sched-cache-fix-a-thread-aggregation-conflict-when-there-is.html) `fix/medium/under_review` — sched/cache: Fix a thread aggregation conflict when there is one runnable task
