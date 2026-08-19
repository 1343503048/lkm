# tag: preempt

共 1 篇

- [sched-20260819-003-sched-migrate-static-key-api-resend](../../2026/08/sched-20260819-003-sched-migrate-static-key-api-resend.md) `fix/low/under_review` — Hongyan Xia 把调度子系统里残留的 deprecated raw `static_key` API 统一迁移到新的 `static_branch_*` API（含 `sched_feat` 数组用 union 包装 true/false 两种类型），无功能变化。RESEND 已拆成独立补丁、paravirt 部分拿到 Ack。纯清理，合入概率高。