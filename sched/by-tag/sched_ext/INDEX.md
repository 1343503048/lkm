# tag: sched_ext

共 8 篇

- [sched-20260728-009](../../2026/07/sched-20260728-009-sched-ext-set-errno-on-enabling-to-enabled-transition-failure.md) `fix/low/under_review` — sched_ext 启用流程中一个极小的错误处理缺陷：当 SCX_ENABLING → SCX_ENABLED 的 cmpxchg 竞态失败时，函数跳转到 err_disable 但 ret 仍为 0，导致内核日志打印 "scx_root_enable() failed (0)" 这样无意义的信息。单行修复，设置 ret = -EBUSY。
- [sched-20260728-002](../../2026/07/sched-20260728-002-sched-ext-nmi-safe-exit-handling.md) `feature/merged_tip` — Tejun Heo 的 5-patch 系列让 sched_ext 的 exit claiming 变为 lock-free 且 NMI-safe，已合入 sched_ext/for-7.3 分支。这解决了 BPF kfunc 在 NMI 中触发 scx_error() 时死锁的问题。
- [sched-20260728-001](../../2026/07/sched-20260728-001-sched-ext-proxy-execution-support-with-sched-ext.md) `feature/under_review` — Andrea Righi (NVIDIA) 发出 15-patch 系列，目标是让 proxy execution（代理执行）与 sched_ext 共存。此前 SCHED_PROXY_EXEC 显式依赖 `!SCHED_CLASS_EXT`，本系列移除该限制，让 BPF 调度器能正确处理 blocked donor 的入队和 DSQ 转移竞态。v1 刚发出，暂无 review。
- [sched-20260726-007](../../2026/07/sched-20260726-007-selftests-sched-ext-make-allowed-cpus-idle-validation-race-free.md) `fix/medium/under_review` — 一组针对 sched_ext idle 跟踪与 selftest 竞态的修复：Kuba Piecuch 先修复 WAKE_SYNC 下 waker CPU 未被标记 busy 导致的 `allowed_cpus` selftest 偶发失败；Andrea Righi 跟进重写 selftest 的 idle 校验为无竞态版本。目标分支 `sched_ext/for-7.2-fixes`，合入可能性
- [sched-20260726-005](../../2026/07/sched-20260726-005-sched-ext-fix-incorrect-scx-pick-idle-cpu-flag-prefix-in-kernel-doc.md) `fix/low/merged_tip` — 一处 kernel-doc 文档 bug 修复：更正 `SCX_PICK_IDLE_CPU_*` 标志的前缀书写错误，已被 Tejun 直接应用到 `sched_ext/for-7.3`。琐碎文档修复，无需跟进。
- [sched-20260726-004](../../2026/07/sched-20260726-004-sched-ext-sparse-annotation-cleanups.md) `fix/low/merged_tip` — Tejun Heo 的 sched_ext sparse 注解清理三连补丁，消除 RCU/锁注解告警，已被直接应用到 `sched_ext/for-7.3`。纯代码质量整理，无需额外跟进。
- [sched-20260726-002](../../2026/07/sched-20260726-002-sched-ext-bound-per-task-reenqueues-and-eject-the-owning-scheduler.md) `feature/under_review` — Tejun Heo 的 sched_ext 自我保护补丁 v2：给单个任务的 re-enqueue 次数设上限，超限即认定 BPF 调度器有缺陷并将其 eject 回退到默认调度。属于提升 SCX 健壮性的防御性机制，方向获认可，合入可能性较高。
- [sched-20260726-001](../../2026/07/sched-20260726-001-sched-make-proxy-execution-compatible-with-sched-ext.md) `feature/under_review` — Andrea Righi 发布的 proxy execution（PE）与 sched_ext 兼容第 9 版（`[PATCHSET v9 sched_ext/for-7.3]`），目标是让 PE 与 sched_ext 共存：当被阻塞任务需要把执行权代理给持锁的 owner，而该 owner 恰好由 SCX 调度器管理时，PE 不能破坏 SCX 的 pick/dispatch 语义。方向已获认可
