# tag: frequency_invariance

共 2 篇

- [sched-20260824-004](../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `discussion/low/under_review` — 本文为增量更新，完整背景见 related_articles 中的文章。作者承认原始 commit message 基于频率不变性的解释不正确，实际问题源自 `d2d5c129d07e` 引入的 `cpuinfo.max_freq` fallback 逻辑。讨论仍在继续。
- [sched-20260821-004](../../2026/08/sched-20260821-004-sched-fair-only-apply-cpufreq-pressure-where-frequency-is-invariant.md) `fix/medium/under_review` — cpufreq pressure 在非频率不变架构上会错误地降低 CPU capacity，导致利用率计算失衡。Wu Jianyong 的修复仅在 `arch_scale_freq_invariant()` 为真时应用 pressure，但 Vincent Guittot 质疑修复的必要性。
