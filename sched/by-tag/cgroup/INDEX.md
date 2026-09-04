# tag: cgroup

共 4 篇

- [sched-20260904-004](../../2026/09/sched-20260904-004.md) `patch_series/medium/under_review` — CFS CPU 带宽的 quota 与 burst 控制当前使内核态写入顺序变得重要：在 quota 无限时配置 burst，会阻止后续有限 quota 安装；先增 burst 再增 quota（burst-first）会以 EINVAL 失败。本系列让配置的 burst 值与当前 quota 解耦，在 CFS 补充运行时间时再施加 quota 相对钳制，并加 selftest + 文档。
- [sched-20260904-003](../../2026/09/sched-20260904-003.md) `patch_series/medium/under_review` — 代理执行分离调度上下文与执行上下文。提交 `aa4f74dfd42b`（"sched: Fix runtime accounting w/ split exec & sched contexts"）使 per-task/线程组运行时间记账跟随真实执行任务，但 cgroup CPU usage 仍记到 donor。当 donor 与执行任务分属不同 cgroup 时，任务执行时间被算到不同 cgroup。本补丁主张 **cgroup CPU usage 应跟随执行上下文**（`rq->curr`），与 per-task/tg/cgroup user/system 记账一致；调度状态仍关联 donor，但 cgroup CPU usage 记到 `rq->curr`。
- [sched-20260903-014](../../2026/09/sched-20260903-014.md) `patch_series/low/under_review` — `ops.cgroup_set_idle()` 用于按 cgroup 设置 idle 偏好。当下发的新值与当前已生效值相同时，无需重复下发该 ops 调用。本系列使之幂等，避免冗余的 BPF 回调与状态切换开销。
- [sched-20260903-008](../../2026/09/sched-20260903-008.md) `patch_series/medium/under_review` — 代理执行分离调度上下文与执行上下文。调度器运行时间记账将 cgroup 时间记到 donor，而 tick 与 vtime 记账在更新 cgroup 字段时却使用执行任务。当 donor 与执行任务分属不同 cgroup 时，会把 donor cgroup 的 `cpu.stat` usage 记给 donor，而 user/system 字段记给执行任务 cgroup，造成统计错乱（donor cgroup 凭空获得 usage 时间，执行 cgroup 获得 system 时间）。