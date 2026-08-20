# tag: cgroup

共 4 篇

- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-008](../../2026/08/sched-20260820-008.md) `fix/low/merged_tip` — 08-19 的 sched_ext 文档两连修在 08-20 推进：① `ei->type → ei->kind` 示例修复已 Applied 到 `sched_ext/for-7.3-fixes`（Fixes `fa48e8d2c7b5`）；② `cgroup CPU knobs are scheduler-dependent` 文档补丁发 v2。
- [sched-20260820-003](../../2026/08/sched-20260820-003.md) `fix/low/under_review` — Michal Koutny（与同日 Liang Luo v2）把 08-19 的「cpu.max 配额未被 BPF 调度器强制时该告警还是文档」讨论落到了文档方案：cgroup-v2.rst 明确 cpu.max/cpu.idle 等 knob 仅在加载的 BPF 调度器实现了对应回调时才对相关任务生效。纯文档，合入概率高。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。