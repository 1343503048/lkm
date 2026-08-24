# tag: schedutil

共 3 篇

- [sched-20260824-004-sched-fair-cpufreq-pressure-invariant](../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — cpufreq 压力（cpufreq pressure）用于向调度器反馈由于频率受限带来的算力损失。
- [sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle](../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review` — 在进入 tickless idle（NOHZ idle）之前，调度器与 cpufreq 之间的协调存在窗口：
- [sched-20260823-009](../../2026/08/sched-20260823-009.md) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：cpufreq pressure 按「可达最高频率/当前可达最高频率」降 capacity，但 utilization 仅在频率不变架构才带匹配 scaling，导致语义不一致。焦点在「是否仅在不 invariant 场景施加 pressure」。合入概率 medium。