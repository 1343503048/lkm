---
layout: default
tag: "bpf"
title: "标签: bpf"
article_count: 4
---

- [sched-20260822-004](/lkm/2026/08/22/sched-20260822-004-sched-ext-fix-spurious-aborts-in-scx-bpf-dsq-move.html) `fix/medium/merged_tip` — Tejun Heo 修复 `scx_bpf_dsq_move()` 中的虚假调度器中止：任务在迭代过程中可能合法地失去所有权（退出或被重新分配）
- [sched-20260821-007](/lkm/2026/08/21/sched-20260821-007-bpf-sched-ext-mark-ops-argument-container-pointer-fields-as-trusted.html) `feature/none/merged_tip` — sched_ext 的 ops 参数容器指针字段被标记为 trusted
- [sched-20260815-015](/lkm/2026/08/15/sched-20260815-015-selftests-sched-ext-fix-flaky-ddsp-failure-tests-on-busy-sys.html) `feature/low/under_review` — selftests/sched_ext: Fix flaky ddsp failure tests on busy systems
- [sched-20260814-008](/lkm/2026/08/14/sched-20260814-008-cgroup-sched-add-bpf-kfuncs-to-read-a-cpu-cgroup-s-stats.html) `feature/none/under_review` — cgroup, sched: add BPF kfuncs to read a cpu cgroup's stats
