# tag: documentation

共 7 篇

- [sched-20260824-003-docs-sched_ext-cgroup-knobs.md](../../2026/08/sched-20260824-003-docs-sched_ext-cgroup-knobs.md) `fix/low/under_review`
- [sched-20260823-006](../../2026/08/sched-20260823-006.md) `fix/low/under_review` — Tao Cui 把 08-19「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」的裁定落地到 sched-ext.rst：v3 新增「Scheduler-Dependent Knobs」小节，说明 knob 经由 ops.cgroup_set_*() 透传、是否生效取决于调度器。纯文档，合入概率高。
- [sched-20260822-006](../../2026/08/sched-20260822-006-sched-ext-sync-headers-and-docs-applied-to-7-3-fixes.md) `fix/low/merged_tip` — 两个 sched_ext 补丁被合入 `sched_ext/for-7.3-fixes`：1) 同步 tools headers 与 scx 仓库保持一致；2) cgroup v2 文档增加 BPF 调度器回调（cpu.max/cpu.idle）说明。
- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。
- [sched-20260819-010](../../2026/08/sched-20260819-010-sched-ext-cgroup-set-bandwidth-warn-vs-doc.md) `discussion/low/under_review` — 关于 "sched_ext 下 cpu.max 配额未被 BPF 调度器强制时是否告警" 的讨论：Tejun NAK 了运行时一次性警告（参照 cpu.weight 前车之鉴），倾向用文档说明 "knob 仅当调度器实现对应回调才生效"。作者改为投文档补丁。属 08-18 带宽讨论的延续。
- [sched-20260819-008](../../2026/08/sched-20260819-008-sched-ext-documentation-fixes-cgroup-knobs-exit-kind.md) `fix/low/under_review` — Liang Luo 修两处 sched-ext 文档：cgroup-v2.rst 里 `cpu.max`/`cpu.max.burst`/`cpu.idle` 应说明也作用于实现了对应回调的 BPF 调度器；sched-ext.rst 示例 `ei->type` 应为 `ei->kind`。纯文档，合入概率高。
