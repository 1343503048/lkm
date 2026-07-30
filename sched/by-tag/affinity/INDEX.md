# tag: affinity

共 2 篇

- [sched-20260726-007](../../2026/07/sched-20260726-007-selftests-sched-ext-make-allowed-cpus-idle-validation-race-free.md) `fix/medium/under_review` — 一组针对 sched_ext idle 跟踪与 selftest 竞态的修复：Kuba Piecuch 先修复 WAKE_SYNC 下 waker CPU 未被标记 busy 导致的 `allowed_cpus` selftest 偶发失败；Andrea Righi 跟进重写 selftest 的 idle 校验为无竞态版本。目标分支 `sched_ext/for-7.2-fixes`，合入可能性
- [sched-20260726-001](../../2026/07/sched-20260726-001-sched-make-proxy-execution-compatible-with-sched-ext.md) `feature/under_review` — Andrea Righi 发布的 proxy execution（PE）与 sched_ext 兼容第 9 版（`[PATCHSET v9 sched_ext/for-7.3]`），目标是让 PE 与 sched_ext 共存：当被阻塞任务需要把执行权代理给持锁的 owner，而该 owner 恰好由 SCX 调度器管理时，PE 不能破坏 SCX 的 pick/dispatch 语义。方向已获认可
