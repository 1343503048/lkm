# tag: frequency_invariance

共 1 篇

- [sched-20260821-004](../../2026/08/sched-20260821-004-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `fix/medium/under_review` — cpufreq pressure 在非频率不变架构上会错误地降低 CPU capacity，导致利用率计算失衡。Wu Jianyong 的修复仅在 `arch_scale_freq_invariant()` 为真时应用 pressure，但 Vincent Guittot 质疑修复的必要性。
