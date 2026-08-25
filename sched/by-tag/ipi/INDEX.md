# tag: ipi

共 1 篇

- [sched-20260821-010](../../2026/08/sched-20260821-010-cpuidle-deny-idle-entry-when-cpu-already-have-ipi-interrupt-pending.md) `fix/medium/under_review` — v2 补丁尝试在 CPU 已有 IPI 中断挂起时阻止进入 idle 状态，但 Daniel Lezcano 认为这应该在 idle loop 而非 cpuidle 框架中处理，Maulik Shah 的 v2 方案方向受到质疑。
