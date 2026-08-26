# tag: preempt

共 22 篇

- [sched-20260823-004](../../2026/08/sched-20260823-004.md) `fix/medium/under_review` — Dongli Zhang（Oracle）RFC：远程 CPU 更新 rq 时可能在 owner vCPU 仍被 host 抢占期间推进 rq->clock，导致 steal 间隔被错误计入。修复为抢占期间把 delta 累积到 `deferred_clock_task`，待 vCPU 重入时一并折回 irq/steal 记账。RFC 阶段，合入概率 medium。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。
- [sched-20260819-003](../../2026/08/sched-20260819-003-sched-migrate-static-key-api-resend.md) `fix/low/under_review` — Hongyan Xia 把调度子系统里残留的 deprecated raw `static_key` API 统一迁移到新的 `static_branch_*` API（含 `sched_feat` 数组用 union 包装 true/false 两种类型），无功能变化。RESEND 已拆成独立补丁、paravirt 部分拿到 Ack。纯清理，合入概率高。
- [sched-20260815-001](../../2026/08/sched-20260815-001-sched-fair-not-goto-more-balance-if-newly-idle-and-has-pendi.md) `feature/medium/under_review` — Xin Zhao 提交 10 个 patch 引入 `LB_PROMOTE` 调度特性，目标是在 `CONFIG_HZ_250` 等低 HZ 嵌入式平台上消除 CFS 任务的"不合理 CPU 空闲"事件（>4ms 调度延迟），提升实时性。目前 v1 刚发出，尚无 maintainer 意见，合入价值取决于通用性论证。
- [sched-20260810-015](../../2026/08/sched-20260810-015-sched-remove-the-unused-preempt-offset-parameter-of-cant-sle.md) `cleanup/low/merged_tip` — Boqun Feng 的 3 个抢占/锁相关清理 commit 已由 tip-bot 合入 `tip/locking/core`（2026-08-10 报告）：移除未使用的 `preempt_offset` 参数、避免有符号比较、arm64 启用 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。merged_tip。
- [sched-20260809-004](../../2026/08/sched-20260809-004-sched-remove-the-unused-preempt-offset-parameter-of-cant-sle.md) `fix/low/merged_tip` — Boqun Feng 的 3 个抢占相关清理/修复已由 tip-bot 合入 `tip/locking/core`（2026-08-09 报告），属已合入主线前的 tip 阶段。无需额外 review。
- [sched-20260807-024-sched-preempt-count-cant-migrate-sleep-cleanup.md](../../2026/08/sched-20260807-024-sched-preempt-count-cant-migrate-sleep-cleanup.md) `in-review`
- [sched-20260807-014-preempt-dynamic-simplify-v2.md](../../2026/08/sched-20260807-014-preempt-dynamic-simplify-v2.md) `in-review`
- [sched-20260806-007](../../2026/08/sched-20260806-007-cpufreq-schedutil-fix-rate-limit-overflow-v3.md) `fix/high/under_review`
- [sched-20260806-006](../../2026/08/sched-20260806-006-sched-cpufreq-schedutil-boost-freq-handling.md) `fix/high/under_review`
- [sched-20260806-004](../../2026/08/sched-20260806-004-sched-core-dont-pin-idle-task-migrate-disable-switch.md) `fix/high/under_review`
- [sched-20260806-003](../../2026/08/sched-20260806-003-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review`
- [sched-20260805-012](../../2026/08/sched-20260805-012-arm64-separate-preempt-resched-bits.md) `feature/under_review`
- [sched-20260805-010](../../2026/08/sched-20260805-010-cpufreq-schedutil-fix-rate-limit-overflow.md) `fix/high/under_review`
- [sched-20260805-003](../../2026/08/sched-20260805-003-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review`
- [sched-20260804-018](../../2026/08/sched-20260804-018-rseq-fix-hard-lockup-granted-time-slice-extension-v3.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。
- [sched-20260804-009](../../2026/08/sched-20260804-009-sched-dynamic-simplify-preempt_dynamic-v2.md) `feature/under_review` — 在 08-03-007 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS` 的基础上，Mark Rutland 进一步简化 PREEMPT_DYNAMIC 的静态键选择与重写逻辑（6 笔 patch），收敛架构分支。这是 08-03-007 的延续，合入可能性 high。
- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
- [sched-20260803-007](../../2026/08/sched-20260803-007-preempt-introduce-has_separate_preempt_resched_bits.md) `feature/under_review` — `preempt` 引入 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`，允许架构把 PREEMPT 与 NEED_RESCHED 位拆分存储，缓解 TIF 位紧张。Peter Zijlstra 要求合并前两 patch，s390 已给 Reviewed-by。合入可能性高。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
- [sched-20260801-007](../../2026/08/sched-20260801-007-sched-preempt-count-cleanups-and-separate-resched-bits.md) `feature/under_review` — Boqun Feng 发出一个 24 patch 的 preempt_count 清理与重构系列，其中三个与调度核心直接相关：两个是 `kernel/sched/core.c` 中调试断言函数的参数与比较清理，一个是为 arm64 打开 `HAS_SEPARATE_PREEMPT_RESCHED_BITS`。改动本身低风险，但作为跨架构大系列，合入取决于整体协调。
- [sched-20260730-009](../../2026/07/sched-20260730-009-sched-dynamic-simplify-preempt-dynamic.md) `feature/under_review` — Mark Rutland 的 5-patch 系列简化 `PREEMPT_DYNAMIC` 配置。Mete Durlu 在 s390 上测试显示 vmlinux 减小约 1MB，bzImage 减小约 32KB，bloat-o-meter 显示净减少约 107KB。无行为变化报告。
