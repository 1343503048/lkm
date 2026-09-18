# tag: wake_affine

共 8 篇

- [sched-20260918-001](../../2026/09/sched-20260918-001-sched-document-wf-sync-wakeup-placement-semantics.md) `feature/rfc` — 增量更新：Shubhang Kaushik 的 WF_SYNC 语义文档系列推出 v2（去掉实现细节、只描述稳定的 fair 类语义），并修正 waitqueue API 中"wakee 不会被迁移"的错误保证。本日 Peter Zijlstra 质疑整篇文档是"bitrot 温床"、建议改成内联注释，Shrikanth Hegde 则支持文档化（WF_SYNC 已有 4+ 个改动提案、语义混乱）
- [sched-20260810-012](../../2026/08/sched-20260810-012-sched-fair-let-sync-wakeups-target-the-waker-s-core.md) `feature/under_review` — Madadi Vineeth Reddy 提交「让同步唤醒目标落在唤醒者所在 core」，附 Kayra Cizmeci 在 8/10 提供的 x86 实测数据（部分负载 IPC/延迟改善）。under_review。
- [sched-20260806-012](../../2026/08/sched-20260806-012-fuse-wakeup-hints-to-scheduler.md) `feature/draft`
- [sched-20260806-009](../../2026/08/sched-20260806-009-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review`
- [sched-20260805-008](../../2026/08/sched-20260805-008-sched-fair-decline-wf_sync-stacking-when-waker-llc-busier.md) `feature/under_review`
- [sched-20260805-007](../../2026/08/sched-20260805-007-sched-fair-wf_sync-semantics-wake-affine-doc.md) `feature/under_review`
- [sched-20260805-006](../../2026/08/sched-20260805-006-sched-fair-sync-wakeup-target-waker-core.md) `feature/under_review`
- [sched-20260804-006](../../2026/08/sched-20260804-006-sched-fair-sync-wakeups-target-waker-core.md) `discussion/under_review` — sync wakeup 优化在 08-04 呈三个并行子方向：选 waker 的 core、保留 wake-affine、非 SMT reciprocal 优先 waker cpu。延续 08-03-004 的「先定义统一 policy」要求，目前仍 medium，需先收敛策略再定补丁定位。
