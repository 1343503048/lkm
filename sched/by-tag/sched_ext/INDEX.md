# tag: sched_ext

共 3 篇

- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。
- [sched-20260820-002](../../2026/08/sched-20260820-002.md) `feature/low/under_review` — Daniel T. Lee 把 sched_ext ops 的几个 container 指针参数（cs/cpuc/dsq/task 的 kptr）从 `PTR_UNTRUSTED` 改为 `PTR_TRUSTED`，因为 ops 调用上下文已保证其可信。用户写 BPF 调度器时不再被迫加冗余检查。已通过 bpf CI，合入概率高。