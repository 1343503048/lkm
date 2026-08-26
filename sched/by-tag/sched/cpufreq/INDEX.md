# tag: sched/cpufreq

共 2 篇

- [sched-20260824-004](../../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `discussion/low/under_review` — 本文为增量更新，完整背景见 related_articles 中的文章。作者承认原始 commit message 基于频率不变性的解释不正确，实际问题源自 `d2d5c129d07e` 引入的 `cpuinfo.max_freq` fallback 逻辑。讨论仍在继续。
- [sched-20260824-002](../../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/low/under_review` — `sugov_hold_freq()` 可能在 runqueue 转空时保持 UCLAMP_MIN 驱动的高频率，若随后 cpuidle 停掉 tick，CPU 将在整个 idle 期间维持不必要的高电压；此补丁在 tick 停止前发出最后一次频率更新。
