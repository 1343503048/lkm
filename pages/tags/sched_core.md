---
layout: default
tag: "sched/core"
title: "标签: sched/core"
article_count: 37
---

- [sched-20260819-002](/lkm/2026/08/19/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.html) `discussion/high/under_review` — Peter 在 8/19 回复 Aaron Lu 7/2 报告的 core_sched pick_task() 竞态：pick_task() 释放 core-w...
- [sched-20260819-003](/lkm/2026/08/19/sched-20260819-003-sched-migrate-static-key-api-resend.html) `fix/low/under_review` — 将调度子系统中直接使用的 raw static_key / static_key_{true,false}() 及 __cfs_bandwidth_used、p...
- [sched-20260819-004](/lkm/2026/08/19/sched-20260819-004-sched-core-remove-balance-callback-cast.html) `fix/low/under_review` — do_balance_callbacks() 中显式函数指针类型转换 (void (*)(struct rq *))head->func 是多余的——它不会改变...
- [sched-20260819-005](/lkm/2026/08/19/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.html) `fix/medium/under_review` — 读 /proc/sys/kernel/sched_rt_runtime_us 在 CONFIG_CPUSETS=n 下因缺少 cpu_hotplug_lock ...
- [sched-20260819-006](/lkm/2026/08/19/sched-20260819-006-sched-rt-cpupri-remove-count-field.html) `fix/low/under_review` — 从 struct cpupri_vec 中删除 count 字段。该字段未被使用（早期 UP 计数用途已无引用），属死代码清理。
- [sched-20260819-011](/lkm/2026/08/19/sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion.html) `feature/low/under_review` — 目标系列：移除 sched_class::balance() 回调（0/2）。8/19 可见多封 Re: 该系列的回复，讨论焦点集中在与 core_sched ...
- [sched-20260818-001](/lkm/2026/08/18/sched-20260818-001-sched-core-skip-rq-avg-idle-update-without-valid-idle-stamp.html) `fix/low/under_review` — sched/core: Skip rq->avg_idle update without a valid idle_stamp
- [sched-20260818-002](/lkm/2026/08/18/sched-20260818-002-sched-ext-proxy-execution-v12-review-discussion.html) `feature/high/under_review` — sched_ext: proxy execution v12 — review discussion (patches 12/17, 14/17)
- [sched-20260818-003](/lkm/2026/08/18/sched-20260818-003-git-pull-sched-ext-changes-for-v7.3.html) `feature/high/merged_tip` — [GIT PULL] sched_ext: Changes for v7.3
- [sched-20260817-003](/lkm/2026/08/17/sched-20260817-003-scheduler-updates-for-v7-3.html) `feature/high/merged_tip` — Scheduler updates for v7.3
- [sched-20260817-001](/lkm/2026/08/16/sched-20260817-001-sched-ext-fix-ops-running-stopping-pairing-for-proxy-exec-do.html) `feature/high/under_review` — sched_ext: Fix ops.running/stopping() pairing for proxy-exec donors
- [sched-20260815-002](/lkm/2026/08/15/sched-20260815-002-sched-ext-make-sched-class-ext-select-generic-allocator.html) `fix/low/merged_tip` — sched_ext: Make SCHED_CLASS_EXT select GENERIC_ALLOCATOR
- [sched-20260814-003](/lkm/2026/08/14/sched-20260814-003-sched-topology-add-a-cpus-read-lock-to-rebuild-sched-domains.html) `fix/medium/under_review` — sched/topology: Add a cpus_read_lock to rebuild_sched_domains()
- [sched-20260814-004](/lkm/2026/08/14/sched-20260814-004-patch-v10-00-12-sched-steal-governor-introduce-preferred-cpu.html) `feature/none/under_review` — [PATCH v10 00/12] sched, steal_governor: Introduce preferred CPUs and steal-driven vCPU backoff
- [sched-20260814-008](/lkm/2026/08/14/sched-20260814-008-cgroup-sched-add-bpf-kfuncs-to-read-a-cpu-cgroup-s-stats.html) `feature/none/under_review` — cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats
- [sched-20260810-001](/lkm/2026/08/10/sched-20260810-001-sched-make-proxy-execution-compatible-with-sched-ext.html) `feature/none/under_review` — sched: Make proxy execution compatible with sched_ext
- [sched-20260810-002](/lkm/2026/08/10/sched-20260810-002-sched-fair-use-list-for-each-entry-rcu-in-print-cfs-stats.html) `fix/medium/under_review` — sched/fair: Use list_for_each_entry_rcu() in print_cfs_stats()
- [sched-20260810-004](/lkm/2026/08/10/sched-20260810-004-perf-core-sched-task-dispatch-and-branch-entry-fixes.html) `fix/medium/under_review` — perf/core: sched_task() dispatch and branch entry fixes
- [sched-20260810-005](/lkm/2026/08/10/sched-20260810-005-perf-core-fix-group-leader-use-after-free-after-sibling-deta.html) `fix/high/merged_tip` — perf/core: Fix group leader use-after-free after sibling detach
- [sched-20260810-006](/lkm/2026/08/10/sched-20260810-006-sched-core-make-core-sched-flips-wait-for-in-flight-selectio.html) `fix/medium/under_review` — sched/core: Make core-sched flips wait for in-flight selections
- [sched-20260810-007](/lkm/2026/08/10/sched-20260810-007-sched-proxy-defer-donor-commit-until-after-proxy-resolution.html) `feature/none/under_review` — sched/proxy: Defer donor commit until after proxy resolution
- [sched-20260810-008](/lkm/2026/08/10/sched-20260810-008-sched-core-try-to-use-a-preferred-cpu-in-is-cpu-allowed.html) `feature/none/under_review` — sched/core: Try to use a preferred CPU in is_cpu_allowed
- [sched-20260810-013](/lkm/2026/08/10/sched-20260810-013-sched-topology-don-t-claim-sched-domain-shared-twice-on-the-.html) `fix/low/under_review` — sched/topology: don't claim sched_domain_shared twice on the same domain
- [sched-20260810-015](/lkm/2026/08/10/sched-20260810-015-sched-remove-the-unused-preempt-offset-parameter-of-cant-sle.html) `cleanup/low/merged_tip` — sched: Remove the unused preempt_offset parameter of __cant_sleep()
- [sched-20260809-001](/lkm/2026/08/09/sched-20260809-001-sched-debug-introduce-per-cpu-debugfs-files.html) `feature/none/under_review` — sched/debug: Introduce per-CPU debugfs files
- [sched-20260809-004](/lkm/2026/08/09/sched-20260809-004-sched-remove-the-unused-preempt-offset-parameter-of-cant-sle.html) `fix/low/merged_tip` — sched: Remove the unused preempt_offset parameter of __cant_sleep()
- [sched-20260809-005](/lkm/2026/08/09/sched-20260809-005-kernel-sched-ext-ext-c-1451-38-sparse-sparse-incorrect-type-.html) `fix/low/under_review` — kernel/sched/ext/ext.c:1451:38: sparse: sparse: incorrect type in initializer (different address spaces)
- [sched-20260809-006](/lkm/2026/08/09/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.html) `bug/high/under_review` — KASAN: slab-use-after-free in owner_on_cpu via iava_remove (mutex optimistic spin) [iavf] [syzkaller]
- [sched-20260808-001-sched-core-skip-avg-idle-v3](/lkm/2026/08/08/sched-20260808-001-sched-core-skip-avg-idle-v3.html) `unknown/none/in-review` — sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新（v3）
- [sched-20260808-002-kcov-scheduler-coverage-leaks](/lkm/2026/08/08/sched-20260808-002-kcov-scheduler-coverage-leaks.html) `unknown/none/in-review` — kcov: 抑制定时器与调度器覆盖泄漏
- [sched-20260807-001-proxy-execution-sleeping-owner-v31](/lkm/2026/08/07/sched-20260807-001-proxy-execution-sleeping-owner-v31.html) `unknown/none/in-review` — Proxy Execution: Sleeping Owner Handling (v31, resend)
- [sched-20260807-006-perf-core-kfree-nolock-sched](/lkm/2026/08/07/sched-20260807-006-perf-core-kfree-nolock-sched.html) `unknown/none/in-review` — perf/core: 用 kfree_nolock() 替代 kfree_rcu()（调度上下文释放）
- [sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx](/lkm/2026/08/07/sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx.html) `unknown/none/in-review` — perf/core: 修复 sched_task() 在纯 CPU-wide 事件下 NULL pmu_ctx 解引用
- [sched-20260807-008-perf-core-sched-task-dispatch-branch-fixes](/lkm/2026/08/07/sched-20260807-008-perf-core-sched-task-dispatch-branch-fixes.html) `unknown/none/in-review` — perf/core: sched_task() dispatch 与 branch entry 修复
- [sched-20260807-013-sched-preserve-reset-on-fork](/lkm/2026/08/07/sched-20260807-013-sched-preserve-reset-on-fork.html) `unknown/none/in-review` — sched: 并发 sched_setparam 下保留 reset-on-fork
- [sched-20260807-019-sched-core-skip-avg-idle-no-idle-stamp](/lkm/2026/08/07/sched-20260807-019-sched-core-skip-avg-idle-no-idle-stamp.html) `unknown/none/in-review` — sched/core: 无有效 idle_stamp 时跳过 rq->avg_idle 更新
- [sched-20260807-024-sched-preempt-count-cant-migrate-sleep-cleanup](/lkm/2026/08/07/sched-20260807-024-sched-preempt-count-cant-migrate-sleep-cleanup.html) `unknown/none/in-review` — sched: 清理 preempt_count 的 __cant_migrate/__cant_sleep 参数
