# tag: sched/fair

共 2 篇

- [sched-20260819-003-sched-migrate-static-key-api-resend](../../2026/08/sched-20260819-003-sched-migrate-static-key-api-resend.md) `fix/low/under_review` — Hongyan Xia 把调度子系统里残留的 deprecated raw `static_key` API 统一迁移到新的 `static_branch_*` API（含 `sched_feat` 数组用 union 包装 true/false 两种类型），无功能变化。RESEND 已拆成独立补丁、paravirt 部分拿到 Ack。纯清理，合入概率高。
- [sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix](../../2026/08/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.md) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group se 的 `load.weight==0`，`__calc_prop_weight()` 除 `cfs_rq->load.weight`），由 `tg_cpus()` 未对 0 做下限导致；同日配套补丁把 `tg_cpus()` 下限取到 1。critical 级崩溃，但仅影响尚未进主线、由发行版（CachyOS）带入的 tip 系列。