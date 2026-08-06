# tag: wake_affine

共 6 篇

- [sched-20260806-009](../../2026/08/sched-20260806-009-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review` — sync wakeup 落到 waker core（Kayra x86 实测）。延续 08-05-006。
- [sched-20260806-012](../../2026/08/sched-20260806-012-fuse-wakeup-hints-to-scheduler.md) `feature/draft` — fuse 唤醒 hint 透传调度器（RFC, ping Miklos）。

- [sched-20260805-006](../../2026/08/sched-20260805-006-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review` — sync wakeup 落到 waker core。延续 08-04-006。
- [sched-20260805-007](../../2026/08/sched-20260805-007-sched-fair-wf_sync-semantics-wake-affine-doc.md) `feature/under_review` — WF_SYNC 语义澄清 + 非 SMT 保留 wake-affine。延续 08-04-006。
- [sched-20260805-008](../../2026/08/sched-20260805-008-sched-fair-decline-wf_sync-stacking-when-waker-llc-busier.md) `feature/under_review` — waker LLC 更忙时拒 WF_SYNC 堆叠（RFC）。延续 08-04-006。

- [sched-20260804-006](../../2026/08/sched-20260804-006-sched-fair-sync-wakeups-target-waker-core.md) `discussion/under_review` — sync wakeup 优化在 08-04 呈三个并行子方向：选 waker 的 core、保留 wake-affine、非 SMT reciprocal 优先 waker cpu。延续 08-03-004 的「先定义统一 policy」要求，目前仍 medium，需先收敛策略再定补丁定位。
