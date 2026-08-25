---
layout: default
tag: "cpuidle"
title: "标签: cpuidle"
article_count: 4
---

- [sched-20260824-001](/lkm/2026/08/24/sched-20260824-001-sched_ext-cgroup-init-cpu-idle.html) `fix/low/under_review` — sched_ext: 在 scx_cgroup_init_args 中传递初始 cpu.idle 状态
- [sched-20260824-002](/lkm/2026/08/24/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.html) `fix/low/under_review` — sched/cpufreq: 在进入 tickless idle 前重新评估频率
- [sched-20260821-010](/lkm/2026/08/21/sched-20260821-010-cpuidle-deny-idle-entry-when-cpu-already-have-ipi-interrupt-pending.html) `fix/medium/under_review` — v2 补丁尝试在 CPU 已有 IPI 中断挂起时阻止进入 idle 状态
- [sched-20260821-011](/lkm/2026/08/21/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.html) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移）
