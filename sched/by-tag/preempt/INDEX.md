# tag: preempt

共 3 篇

- [sched-20260824-008-sched-core-defer-vcpu-task-clock](../../2026/08/sched-20260824-008-sched-core-defer-vcpu-task-clock.md) `fix/medium/under_review` — 当远端 vCPU 被抢占时，其 task clock 的更新若立即进行会带来额外的跨核开销与
- [sched-20260823-004](../../2026/08/sched-20260823-004.md) `fix/medium/under_review` — Dongli Zhang（Oracle）RFC：远程 CPU 更新 rq 时可能在 owner vCPU 仍被 host 抢占期间推进 rq->clock，导致 steal 间隔被错误计入。修复为抢占期间把 delta 累积到 `deferred_clock_task`，待 vCPU 重入时一并折回 irq/steal 记账。RFC 阶段，合入概率 medium。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。