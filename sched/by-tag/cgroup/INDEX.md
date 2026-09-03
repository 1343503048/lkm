# tag: cgroup

共 2 篇

- [sched-20260903-014](../../2026/09/sched-20260903-014.md) `patch_series/low/under_review` — `ops.cgroup_set_idle()` 用于按 cgroup 设置 idle 偏好。当下发的新值与当前已生效值相同时，无需重复下发该 ops 调用。本系列使之幂等，避免冗余的 BPF 回调与状态切换开销。
- [sched-20260903-008](../../2026/09/sched-20260903-008.md) `patch_series/medium/under_review` — 代理执行分离调度上下文与执行上下文。调度器运行时间记账将 cgroup 时间记到 donor，而 tick 与 vtime 记账在更新 cgroup 字段时却使用执行任务。当 donor 与执行任务分属不同 cgroup 时，会把 donor cgroup 的 `cpu.stat` usage 记给 donor，而 user/system 字段记给执行任务 cgroup，造成统计错乱（donor cgroup 凭空获得 usage 时间，执行 cgroup 获得 system 时间）。