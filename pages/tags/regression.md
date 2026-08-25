---
layout: default
tag: "regression"
title: "标签: regression"
article_count: 9
---

- [sched-20260823-002](/lkm/2026/08/23/sched-20260823-002.html) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fa...
- [sched-20260820-004](/lkm/2026/08/20/sched-20260820-004.html) `bug/low/under_review` — LKP sparse 在 `kernel/sched/fair.c:2004`（enqueue 路径判断 `cfs_rq->nr_running`）发出静...
- [sched-20260820-010](/lkm/2026/08/20/sched-20260820-010.html) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WAR...
- [sched-20260819-001](/lkm/2026/08/19/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.html) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group ...
- [sched-20260815-013](/lkm/2026/08/15/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html) `regression/high/under_review` — sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)
- [sched-20260730-002](/lkm/2026/07/30/sched-20260730-002-sched-fair-cgroup-mode-default-netperf-regression.html) `bug/high/under_review` — [linux-next:master] [sched/fair]  fb1050ac8e: netperf.Throughput_Mbps 14.6% regression
- [sched-20260730-003](/lkm/2026/07/30/sched-20260730-003-sched-idle-sysbench-regression-f4c31b07b136.html) `bug/high/under_review` — sched/idle: Sysbench threads regression after f4c31b07b136
- [sched-20260729-003](/lkm/2026/07/29/sched-20260729-003-sched-idle-stop-the-tick-when-no-cpuidle-driver-is-available.html) `fix/high/under_review` — sched/idle: Stop the tick when no cpuidle driver is available
- [sched-20260728-010](/lkm/2026/07/28/sched-20260728-010-sched-idle-sysbench-threads-regression-after-f4c31b07b136.html) `bug/high/under_review` — sched idle sysbench threads regression after f4c31b07b136
