# tag: proxy_execution

共 9 篇

- [sched-20260818-002](../../2026/08/sched-20260818-002-sched-ext-proxy-execution-v12-review-discussion.md) `feature/high/under_review` — 本文为增量更新。Andrea Righi 的 v12 proxy-exec + sched_ext 共存系列（17 patch）本日继续收到 Tejun Heo 对 patch 12/17（remote DSQ transfers）和 14/17（proxy donor admission）的详细 review，Andrea 逐条回应并承诺调整。关键进展：Tejun 同意去掉 `SCX_TASK_
- [sched-20260817-001](../../2026/08/sched-20260817-001-sched-ext-fix-ops-running-stopping-pairing-for-proxy-exec-do.md) `feature/high/under_review` — Andrea Righi 的 v12（17 patch，2024 行）让 **proxy execution 与 sched_ext 共存**——此前二者在构建期互斥（`CONFIG_SCHED_PROXY_EXEC` 与 `CONFIG_SCHED_CLASS_EXT` 不能同时开）。通过新增 per-scheduler 能力 `SCX_OPS_ENQ_BLOCKED`，BPF 调度器可控制是否
- [sched-20260810-007](../../2026/08/sched-20260810-007-sched-proxy-defer-donor-commit-until-after-proxy-resolution.md) `feature/under_review` — Xukai Wang 提交 RFC v2「sched/proxy: Defer donor commit until after proxy resolution」。把 donor 任务的 commit（成为 rq->curr）推迟到 proxy 解析完成后，避免中途状态被负载均衡/统计看到。RFC 阶段，合入可能性低（依赖 proxy 主线）。
- [sched-20260810-001](../../2026/08/sched-20260810-001-sched-make-proxy-execution-compatible-with-sched-ext.md) `feature/under_review` — Andrea Righi 提交 v11「Make proxy execution compatible with sched_ext」——15 个 patch，为 BPF 调度器引入 donor/owner 任务选择抽象，使其能正确参与 proxy execution。目前 under_review。
- [sched-20260809-004](../../2026/08/sched-20260809-004-sched-remove-the-unused-preempt-offset-parameter-of-cant-sle.md) `fix/low/merged_tip` — Boqun Feng 的 3 个抢占相关清理/修复已由 tip-bot 合入 `tip/locking/core`（2026-08-09 报告），属已合入主线前的 tip 阶段。无需额外 review。
- [sched-20260807-001-proxy-execution-sleeping-owner-v31.md](../../2026/08/sched-20260807-001-proxy-execution-sleeping-owner-v31.md) `in-review`
- [sched-20260806-010](../../2026/08/sched-20260806-010-sched-ext-proxy-execution-conservative-terminate.md) `feature/under_review`
- [sched-20260805-001](../../2026/08/sched-20260805-001-sched-ext-proxy-exec-reject-dsq-class-transition.md) `feature/under_review`
- [sched-20260804-001](../../2026/08/sched-20260804-001-sched-ext-enable-proxy-execution-with-sched_ext.md) `feature/under_review` — Andrea Righi 的 15-patch 系列把内核主流的 SCHED_PROXY_EXEC（代理执行）机制带到 sched_ext：互斥锁/RT 阻塞的任务可被同调度类或更早调度类的高优先级任务「代理执行」，从而缓解优先级反转。Tejun 评价「Nice.」并指出两处需澄清的语义。属大型 feature，合入可能性高，仍处 review。
