# tag: psi

共 7 篇

- [sched-20260823-007](../../2026/08/sched-20260823-007.md) `feature/low/under_review` — Tao Cui 的 cgroup PSI selftest 推进到 v4：改成 kselftest harness（TEST_F/FIXTURE_SETUP/TEARDOWN），并把「poll 超时未触发」从 SKIP 改为 FAIL。已迭代四轮，合入概率高。
- [sched-20260819-007](../../2026/08/sched-20260819-007-selftests-cgroup-add-psi-pressure-tests-v3.md) `feature/low/under_review` — Tao Cui 为 cgroup selftests 增加 `test_psi.c`，覆盖 PSI 压力触发与 `cgroup.pressure` 显隐切换，v3 按 review 拆分成 per-resource case 并提升健壮性。纯测试覆盖增强，合入概率高。
- [sched-20260807-012-psi-rtpoll-teardown-stale-timer.md](../../2026/08/sched-20260807-012-psi-rtpoll-teardown-stale-timer.md) `in-review`
- [sched-20260807-011-psi-use-ffs-task-count-bitmask.md](../../2026/08/sched-20260807-011-psi-use-ffs-task-count-bitmask.md) `in-review`
- [sched-20260804-016](../../2026/08/sched-20260804-016-sched-psi-skip-cpus-zero-non-idle-delta.md) `feature/low/under_review` — PSI 统计中对非 idle 时间增量为 0 的 CPU 仍走完整更新路径，Dmitry Pletnev 改为跳过以减开销（大量 idle CPU 的系统受益明显）。低严重度优化，合入可能性 medium，需确认边界正确性。
- [sched-20260728-008](../../2026/07/sched-20260728-008-sched-psi-fix-32-bit-overflow-in-trigger-window.md) `fix/medium/under_review` — PSI（Pressure Stall Information）trigger 机制在 32 位架构上存在两处整数溢出 bug，导致用户配置的大阈值/窗口（如 4s/6s）被截断为错误值，trigger 监控行为与预期不符。目前 v1 已发出并有社区成员确认问题，等待 maintainer review。
- [sched-20260728-007](../../2026/07/sched-20260728-007-docs-accounting-psi-drop-stale-500ms-window-minimum-from-tri.md) `discussion/low/under_review` — PSI 文档修复补丁的讨论：作者 Tao 计划发 v2，保留 window-range 修复但恢复 system-wide 和 cgroup 文件的统一措辞。此前 commit 8b39d20eceed 已 revert 了 cgroup-specific gating，所以 2s-multiple 规则对两者统一适用。
