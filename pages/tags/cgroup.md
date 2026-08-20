---
layout: default
tag: "cgroup"
title: "标签: cgroup"
article_count: 17
---

- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — 配套修复补丁 tg_cpus() 在 cpuset 为空时返回 0，使 shares_max 归零绕过 MIN_SHARES 下限，导致 group se 的 ...
- [sched-20260819-007](/lkm/2026/08/19/sched-20260819-007-selftests-cgroup-add-psi-pressure-tests-v3.html) `feature/low/under_review` — 为 cgroup selftests 新增 test_psi.c：per-resource（io/memory/cpu/irq）PSI 触发烟测（每 fd 一个...
- [sched-20260819-008](/lkm/2026/08/19/sched-20260819-008-sched-ext-documentation-fixes-cgroup-knobs-exit-kind.html) `fix/low/under_review` — sched-ext 文档两连修：(1) 把 cpu.max / cpu.max.burst / cpu.idle 的描述从'仅影响 fair-class'改为'...
- [sched-20260819-010](/lkm/2026/08/19/sched-20260819-010-sched-ext-cgroup-set-bandwidth-warn-vs-doc.html) `discussion/low/under_review` — 原 RFC 提议：当 cgroup 配了有限 cpu.max 配额但当前 BPF 调度器未实现 cgroup_set_bandwidth 回调时，打印一次性警告...
- [sched-20260818-004](/lkm/2026/08/18/sched-20260818-004-sched-ext-allow-ops-cgroup-set-bandwidth-to-be-sleepable.html) `feature/medium/under_review` — sched_ext: allow ops.cgroup_set_bandwidth() to be sleepable
- [sched-20260818-005](/lkm/2026/08/18/sched-20260818-005-sched-flatten-the-pick-v3-benchmarks.html) `feature/medium/under_review` — sched: Flatten the pick — v3 s390 benchmark results
- [sched-20260817-003](/lkm/2026/08/17/sched-20260817-003-scheduler-updates-for-v7-3.html) `feature/high/merged_tip` — Scheduler updates for v7.3
- [sched-20260815-014](/lkm/2026/08/15/sched-20260815-014-sched-fair-fix-flat-hierarchy.html) `fix/low/merged_tip` — sched/fair: Fix flat hierarchy
- [sched-20260814-008](/lkm/2026/08/14/sched-20260814-008-cgroup-sched-add-bpf-kfuncs-to-read-a-cpu-cgroup-s-stats.html) `feature/none/under_review` — cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats
- [sched-20260807-002-sched-ext-find-parent-sched-null-check](/lkm/2026/08/07/sched-20260807-002-sched-ext-find-parent-sched-null-check.html) `unknown/none/in-review` — sched_ext: find_parent_sched() 健壮性修复（NULL 检查争议）
- [sched-20260807-013-sched-preserve-reset-on-fork](/lkm/2026/08/07/sched-20260807-013-sched-preserve-reset-on-fork.html) `unknown/none/in-review` — sched: 并发 sched_setparam 下保留 reset-on-fork
- [sched-20260805-004](/lkm/2026/08/05/sched-20260805-004-sched-fair-remove-dead-throttled-check-pick-task-fair.html) `cleanup/low/superseded` — sched fair remove dead throttled check pick task fair
- [sched-20260804-004](/lkm/2026/08/04/sched-20260804-004-sched-ext-fixes-for-v7.2-rc6-pull.html) `fix/high/merged_tip` — sched_ext: Fix idle CPU state initialization and validation
- [sched-20260803-003](/lkm/2026/08/03/sched-20260803-003-sched-ext-fixes-for-v7.2-rc6.html) `fix/high/merged_tip` — cgroup: Fixes for v7.2-rc6
- [sched-20260801-001](/lkm/2026/08/01/sched-20260801-001-sched-ext-bandwidth-limited-rescue-execution.html) `feature/none/under_review` — sched_ext: Sync tools autogen enum headers
- [sched-20260730-001](/lkm/2026/07/30/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.html) `fix/medium/under_review` — sched/deadline: Skip bandwidth accounting with SCHED_FLAG_KEEP_PARAMS
- [sched-20260730-002](/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html) `bug/high/under_review` — [linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6% regression
