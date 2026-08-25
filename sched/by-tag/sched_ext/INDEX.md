# tag: sched_ext

共 4 篇

- [sched-20260825-004-sched_ext-fix-kernel-doc-finish-dispatch](../../2026/08/sched-20260825-004-sched_ext-fix-kernel-doc-finish-dispatch.md) `fix/low/under_review` — `finish_dispatch()` 的 kernel-doc 注释缺失了 `@slice` 与 `@vtime` 两个参数的描述，
- [sched-20260825-003-sched_ext-serialize-cgroup-knob-updates](../../2026/08/sched-20260825-003-sched_ext-serialize-cgroup-knob-updates.md) `fix/medium/merged_tip` — sched_ext 的 cgroup knob（weight/idle 等）更新存在并发竞态：并发写 `cpu.shares` 等
- [sched-20260825-002-sched_ext-cgroup-set-sleepable](../../2026/08/sched-20260825-002-sched_ext-cgroup-set-sleepable.md) `feature/low/under_review` — `sched_ext` 的 `ops.cgroup_set_weight()` / `ops.cgroup_set_idle()` 回调当前要求
- [sched-20260825-001-sched_ext-cgroup-init-sched-idle-v3](../../2026/08/sched-20260825-001-sched_ext-cgroup-init-sched-idle-v3.md) `fix/low/under_review` — sched_ext 的 `scx_cgroup_init_args` 会把 cgroup 的初始 weight、带宽控制参数带给