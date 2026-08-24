# tag: documentation

共 4 篇

- [sched-20260824-003-docs-sched_ext-cgroup-knobs](../../2026/08/sched-20260824-003-docs-sched_ext-cgroup-knobs.md) `fix/low/under_review` — sched_ext 允许每个 cgroup 设置调度器相关的 CPU 参数（scheduler-dependent knobs），
- [sched-20260823-006](../../2026/08/sched-20260823-006.md) `fix/low/under_review` — Tao Cui 把 08-19「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」的裁定落地到 sched-ext.rst：v3 新增「Scheduler-Dependent Knobs」小节，说明 knob 经由 ops.cgroup_set_*() 透传、是否生效取决于调度器。纯文档，合入概率高。
- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。