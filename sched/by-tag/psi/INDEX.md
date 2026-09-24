# tag: psi

共 11 篇

- [sched-20260924-012](../../2026/09/sched-20260924-012-sched-core-account-psi-irq-time-to-the-execution-context-not.md) `fix/low/merged_tip` — - sched-20260918-018 / sched-20260919-005 / sched-20260922-014：Zhan Xusheng 的「把 PSI IRQ 时间计入执行上下文」补丁，与 Peter Zijlstra 多轮往返后被确认合入。 - sched-20260924-012（今天，合并确认）：tip-bot2 发出正式合入通知——该补丁已进 tip 的 `sched/ur
- [sched-20260922-014](../../2026/09/sched-20260922-014-sched-core-account-psi-irq-time-to-the-execution-context.md) `fix/low/merged_tip` — 本文为增量更新，完整背景见 sched-20260918-018 与 sched-20260919-005。Zhan Xusheng 的「把 PSI IRQ 时间计入执行上下文」补丁当天完成与 Peter Zijlstra 的来回：先因应用分支问题被拒，经作者指出依赖 commit `f5741d2b3451` 只在 sched/urgent/master、不在 sched/core 后，Pete
- [sched-20260919-005](../../2026/09/sched-20260919-005-sched-core-account-psi-irq-time-to-the-execution-context.md) `fix/low/under_review` — 增量更新：Zhan Xusheng 的 proxy execution PSI IRQ 记账修复本日获 Hui Su 的 Tested-by——作者实测补丁把 IRQ 时间归属从 donor 移到执行上下文（`rq->curr`），且补上了原测试缺失的 donor != curr 场景。定量的 irq.pressure 归属迁移数据支持修复方向，系列等待维护者收取。
- [sched-20260918-018](../../2026/09/sched-20260918-018-sched-core-account-psi-irq-time-to-the-execution-context.md) `fix/low/under_review` — Zhan Xusheng 提交修复：proxy execution 下 `sched_tick()` 把 PSI IRQ 时间记到 `rq->donor`，而 `__schedule()` 记到 `rq->curr`，二者不一致导致 IRQ 时间被记到错误的 cgroup。修复是让 `sched_tick()` 改传 `rq->curr`（恢复 split 之前的语义）。仅影响 `CONFIG_S
- [sched-20260823-007](../../2026/08/sched-20260823-007.md) `feature/low/under_review` — Tao Cui 的 cgroup PSI selftest 推进到 v4：改成 kselftest harness（TEST_F/FIXTURE_SETUP/TEARDOWN），并把「poll 超时未触发」从 SKIP 改为 FAIL。已迭代四轮，合入概率高。
- [sched-20260819-007](../../2026/08/sched-20260819-007-selftests-cgroup-add-psi-pressure-tests-v3.md) `feature/low/under_review` — Tao Cui 为 cgroup selftests 增加 `test_psi.c`，覆盖 PSI 压力触发与 `cgroup.pressure` 显隐切换，v3 按 review 拆分成 per-resource case 并提升健壮性。纯测试覆盖增强，合入概率高。
- [sched-20260807-012-psi-rtpoll-teardown-stale-timer.md](../../2026/08/sched-20260807-012-psi-rtpoll-teardown-stale-timer.md) `in-review`
- [sched-20260807-011-psi-use-ffs-task-count-bitmask.md](../../2026/08/sched-20260807-011-psi-use-ffs-task-count-bitmask.md) `in-review`
- [sched-20260804-016](../../2026/08/sched-20260804-016-sched-psi-skip-cpus-zero-non-idle-delta.md) `feature/low/under_review` — PSI 统计中对非 idle 时间增量为 0 的 CPU 仍走完整更新路径，Dmitry Pletnev 改为跳过以减开销（大量 idle CPU 的系统受益明显）。低严重度优化，合入可能性 medium，需确认边界正确性。
- [sched-20260728-008](../../2026/07/sched-20260728-008-sched-psi-fix-32-bit-overflow-in-trigger-window.md) `fix/medium/under_review` — PSI（Pressure Stall Information）trigger 机制在 32 位架构上存在两处整数溢出 bug，导致用户配置的大阈值/窗口（如 4s/6s）被截断为错误值，trigger 监控行为与预期不符。目前 v1 已发出并有社区成员确认问题，等待 maintainer review。
- [sched-20260728-007](../../2026/07/sched-20260728-007-docs-accounting-psi-drop-stale-500ms-window-minimum-from-tri.md) `discussion/low/under_review` — PSI 文档修复补丁的讨论：作者 Tao 计划发 v2，保留 window-range 修复但恢复 system-wide 和 cgroup 文件的统一措辞。此前 commit 8b39d20eceed 已 revert 了 cgroup-specific gating，所以 2s-multiple 规则对两者统一适用。
