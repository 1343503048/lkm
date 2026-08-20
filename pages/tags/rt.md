---
layout: default
tag: "rt"
title: "标签: rt"
article_count: 6
---

- [sched-20260819-005](/lkm/2026/08/19/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.html) `fix/medium/under_review` — 读 /proc/sys/kernel/sched_rt_runtime_us 在 CONFIG_CPUSETS=n 下因缺少 cpu_hotplug_lock ...
- [sched-20260819-006](/lkm/2026/08/19/sched-20260819-006-sched-rt-cpupri-remove-count-field.html) `fix/low/under_review` — 从 struct cpupri_vec 中删除 count 字段。该字段未被使用（早期 UP 计数用途已无引用），属死代码清理。
- [sched-20260817-003](/lkm/2026/08/17/sched-20260817-003-scheduler-updates-for-v7-3.html) `feature/high/merged_tip` — Scheduler updates for v7.3
- [sched-20260815-013](/lkm/2026/08/15/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html) `regression/high/under_review` — sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)
- [sched-20260809-005](/lkm/2026/08/09/sched-20260809-005-kernel-sched-ext-ext-c-1451-38-sparse-sparse-incorrect-type-.html) `fix/low/under_review` — kernel/sched/ext/ext.c:1451:38: sparse: sparse: incorrect type in initializer (different address spaces)
- [sched-20260804-008](/lkm/2026/08/04/sched-20260804-008-sched-rt-minor-cleanups.html) `cleanup/low/under_review` — sched rt minor cleanups
