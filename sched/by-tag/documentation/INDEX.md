# tag: documentation

共 2 篇

- [sched-20260819-010-sched-ext-cgroup-set-bandwidth-warn-vs-doc](../../2026/08/sched-20260819-010-sched-ext-cgroup-set-bandwidth-warn-vs-doc.md) `discussion/low/under_review` — 关于 "sched_ext 下 cpu.max 配额未被 BPF 调度器强制时是否告警" 的讨论：Tejun NAK 了运行时一次性警告（参照 cpu.weight 前车之鉴），倾向用文档说明 "knob 仅当调度器实现对应回调才生效"。作者改为投文档补丁。属 08-18 带宽讨论的延续。
- [sched-20260819-008-sched-ext-documentation-fixes-cgroup-knobs-exit-kind](../../2026/08/sched-20260819-008-sched-ext-documentation-fixes-cgroup-knobs-exit-kind.md) `fix/low/under_review` — Liang Luo 修两处 sched-ext 文档：cgroup-v2.rst 里 `cpu.max`/`cpu.max.burst`/`cpu.idle` 应说明也作用于实现了对应回调的 BPF 调度器；sched-ext.rst 示例 `ei->type` 应为 `ei->kind`。纯文档，合入概率高。