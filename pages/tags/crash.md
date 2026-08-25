---
layout: default
tag: "crash"
title: "标签: crash"
article_count: 15
---

- [sched-20260823-002](/lkm/2026/08/23/sched-20260823-002.html) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fa...
- [sched-20260823-003](/lkm/2026/08/23/sched-20260823-003.html) `bug/critical/under_review` — arm64 长运行服务器上偶发 `rq->curr != current`（rq 上记录的当前任务与实际 current 不一致）
- [sched-20260820-005](/lkm/2026/08/20/sched-20260820-005.html) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-...
- [sched-20260820-010](/lkm/2026/08/20/sched-20260820-010.html) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WAR...
- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group ...
- [sched-20260819-002](/lkm/2026/08/19/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.html) `discussion/high/under_review` — core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续
- [sched-20260815-005](/lkm/2026/08/15/sched-20260815-005-sched-ext-dispatch-path-follow-ups.html) `fix/medium/under_review` — sched_ext: Dispatch path follow-ups
- [sched-20260815-008](/lkm/2026/08/15/sched-20260815-008-sched-ext-don-t-rehome-a-dead-task-in-scx-cgroup-task-migrat.html) `fix/medium/stale` — sched_ext: don't rehome a dead task in scx_cgroup_task_migrated
- [sched-20260815-009](/lkm/2026/08/15/sched-20260815-009-sched-ext-fix-exit-task-leak-on-fork-failure-during-enable.html) `fix/medium/merged_tip` — sched_ext: Fix exit_task leak on fork failure during enable
- [sched-20260810-003](/lkm/2026/08/10/sched-20260810-003-sched-debug-validate-writes-to-the-scan-size-mb-debugfs-knob.html) `fix/high/under_review` — sched/debug: Validate writes to the scan_size_mb debugfs knob
- [sched-20260810-005](/lkm/2026/08/10/sched-20260810-005-perf-core-fix-group-leader-use-after-free-after-sibling-deta.html) `fix/high/merged_tip` — perf/core: Fix group leader use-after-free after sibling detach
- [sched-20260809-006](/lkm/2026/08/09/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.html) `bug/high/under_review` — KASAN: slab-use-after-free in owner_on_cpu via iava_remove (mutex optimistic spin) [iavf] [syzkaller]
- [sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx](/lkm/2026/08/07/sched-20260807-007-perf-core-sched-task-cpu-wide-null-pmu-ctx.html) `unknown/none/in-review` — perf core sched task cpu wide null pmu ctx
- [sched-20260807-009-perf-core-group-leader-use-after-free](/lkm/2026/08/07/sched-20260807-009-perf-core-group-leader-use-after-free.html) `unknown/none/in-review` — perf core group leader use after free
- [sched-20260807-021-selftests-sched-ext-exit-skeleton-open](/lkm/2026/08/07/sched-20260807-021-selftests-sched-ext-exit-skeleton-open.html) `unknown/none/in-review` — selftests sched ext exit skeleton open
