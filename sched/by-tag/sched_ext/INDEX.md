# tag: sched_ext

共 10 篇

- [sched-20260824-005-sched-lift-cgroup-locking-core](../../2026/08/sched-20260824-005-sched-lift-cgroup-locking-core.md) `fix/medium/under_review` — cgroup 调度相关的更新锁原本分散在 fair/rt 等具体类中，导致 sched_ext 等路径
- [sched-20260824-003-docs-sched_ext-cgroup-knobs](../../2026/08/sched-20260824-003-docs-sched_ext-cgroup-knobs.md) `fix/low/under_review` — sched_ext 允许每个 cgroup 设置调度器相关的 CPU 参数（scheduler-dependent knobs），
- [sched-20260824-001-sched_ext-cgroup-init-cpu-idle](../../2026/08/sched-20260824-001-sched_ext-cgroup-init-cpu-idle.md) `fix/low/under_review` — sched_ext 的 cgroup 支持在向调度器传递 cgroup 初始化参数（scx_cgroup_init_args）时，
- [sched-20260823-008](../../2026/08/sched-20260823-008.md) `fix/low/merged_tip` — `sched_ext Sync common/compat headers` 系列（08-19 009）的跟进回复：确认 `__scx_prolog_disables_migration` 默认值与「err high」注释不一致，在 cherry-pick 8e4f0b1ebcf2 的内核上 `is_migration_disabled(current)` 会少报。Changwoo 已在 scx 侧提 PR scx#3766 修正，Tejun 将 re-sync。属头同步系列的后续打磨。
- [sched-20260823-006](../../2026/08/sched-20260823-006.md) `fix/low/under_review` — Tao Cui 把 08-19「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」的裁定落地到 sched-ext.rst：v3 新增「Scheduler-Dependent Knobs」小节，说明 knob 经由 ops.cgroup_set_*() 透传、是否生效取决于调度器。纯文档，合入概率高。
- [sched-20260823-005](../../2026/08/sched-20260823-005.md) `fix/medium/merged_tip` — Tejun 已将 `sched_ext: Fix spurious aborts in scx_bpf_dsq_move() on ownership change races` Applied 到 `sched_ext/for-7.3-fixes`。修复 DSQ 所有权变更竞态下 `scx_bpf_dsq_move()` 的虚假中止。已 merged，合入可能性 merged。
- [sched-20260823-001](../../2026/08/sched-20260823-001.md) `fix/medium/under_review` — Michal Blaszczyk 修一个 CFS/SCX cgroup 参数「三视图发散」竞态：并发写 cpu.shares 等控制文件时，CFS 内部锁在调 SCX 回调前释放，允许多线程穿插，使 CFS 记录值、SCX 簿记、BPF 调度器三者拿到不同参数。v3 把锁上移到 core 层统一串行化。合入概率高。
- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。
- [sched-20260820-002](../../2026/08/sched-20260820-002.md) `feature/low/under_review` — Daniel T. Lee 把 sched_ext ops 的几个 container 指针参数（cs/cpuc/dsq/task 的 kptr）从 `PTR_UNTRUSTED` 改为 `PTR_TRUSTED`，因为 ops 调用上下文已保证其可信。用户写 BPF 调度器时不再被迫加冗余检查。已通过 bpf CI，合入概率高。