# tag: wake_affine

共 7 篇

- [sched-20260810-012](../../2026/08/sched-20260810-012-sched-fair-let-sync-wakeups-target-the-waker-s-core.md) `feature/under_review` — Madadi Vineeth Reddy 提交「让同步唤醒目标落在唤醒者所在 core」，附 Kayra Cizmeci 在 8/10 提供的 x86 实测数据（部分负载 IPC/延迟改善）。under_review。
- [sched-20260806-012](../../2026/08/sched-20260806-012-fuse-wakeup-hints-to-scheduler.md) `feature/draft`
- [sched-20260806-009](../../2026/08/sched-20260806-009-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review`
- [sched-20260805-008](../../2026/08/sched-20260805-008-sched-fair-decline-wf_sync-stacking-when-waker-llc-busier.md) `feature/under_review`
- [sched-20260805-007](../../2026/08/sched-20260805-007-sched-fair-wf_sync-semantics-wake-affine-doc.md) `feature/under_review`
- [sched-20260805-006](../../2026/08/sched-20260805-006-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review`
- [sched-20260804-006](../../2026/08/sched-20260804-006-sched-fair-sync-wakeups-target-waker-core.md) `discussion/under_review` — sync wakeup 优化在 08-04 呈三个并行子方向：选 waker 的 core、保留 wake-affine、非 SMT reciprocal 优先 waker cpu。延续 08-03-004 的「先定义统一 policy」要求，目前仍 medium，需先收敛策略再定补丁定位。
