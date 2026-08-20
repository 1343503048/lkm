---
layout: default
tag: "regression"
title: "标签: regression"
article_count: 6
---

- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — 配套修复补丁 tg_cpus() 在 cpuset 为空时返回 0，使 shares_max 归零绕过 MIN_SHARES 下限，导致 group se 的 ...
- [sched-20260815-013](/lkm/2026/08/15/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html) `regression/high/under_review` — sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)
- [sched-20260730-002](/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html) `bug/high/under_review` — [linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6% regression
- [sched-20260730-003](/lkm/2026/07/30/sched-20260730-003-sched-idle-sysbench-regression-f4c31b07b136.html) `bug/high/under_review` — sched/idle: Sysbench threads regression after f4c31b07b136
- [sched-20260729-003](/lkm/2026/07/29/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.html) `fix/high/under_review` — sched/idle: Stop the tick when no cpuidle driver is available
- [sched-20260728-010](/lkm/2026/07/28/sched-20260728-010-sched-idle-sysbench-threads-regression-after-f4c31b07b136.html) `bug/high/under_review` — sched idle sysbench threads regression after f4c31b07b136
