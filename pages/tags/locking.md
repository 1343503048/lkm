---
layout: default
tag: "locking"
title: "标签: locking"
article_count: 4
---

- [sched-20260821-002](/lkm/2026/08/21/sched-20260821-002-sched-allow-sleeping-spinlocks-on-preempt-rt-within-non-block.html) `fix/low/under_review` — sched: Allow sleeping spinlocks on PREEMPT_RT within non_block_start()/end block.
- [sched-20260821-009](/lkm/2026/08/21/sched-20260821-009-futex-fix-might-sleep-warning-in-futex-pivot-pending.html) `fix/medium/merged_tip` — futex: Fix might_sleep() warning in futex_pivot_pending()
- [sched-20260815-013](/lkm/2026/08/15/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.html) `regression/high/under_review` — sched/rt: NO_RT_PUSH_IPI causes multi-second PI-boost starvation in pro-audio workloads (dd29c017aed6)
- [sched-20260809-006](/lkm/2026/08/09/sched-20260809-006-kasan-slab-use-after-free-in-owner-on-cpu-via-iava-remove-mu.html) `bug/high/under_review` — KASAN: slab-use-after-free in owner_on_cpu via iava_remove (mutex optimistic spin) [iavf] [syzkaller]
