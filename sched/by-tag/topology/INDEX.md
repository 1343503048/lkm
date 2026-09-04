# tag: topology

共 4 篇

- [sched-20260904-012](../../2026/09/sched-20260904-012.md) `patch_series/medium/under_review` — 延续 09-03 002 的 steal_governor v12（13 补丁系列），本日收到第 01/13 补丁 "sched/cputime: Add kcpustat_field_total helper" 的复审（Re）。该 helper 供 steal_governor 统计 steal time 总量使用，便于在虚拟化场景对 vCPU steal time 设上限并驱动更优的 CPU 选择。
- [sched-20260904-002](../../2026/09/sched-20260904-002.md) `patch_series/medium/under_review` — NVIDIA Olympus 以两个对称 PE 实现 SMT：仅一个 PE 活跃时核为单线程模式、可用全部资源；两个 PE 活跃则共享资源。且 sibling 空闲后从双线程回到单线程模式并非即时。本系列（v2，含封面 79146 + 2/2 "Honor asymmetric SMT priority in idle selection"）让空闲 CPU 选择尊重 `SD_ASYM_PACKING`，优先把任务放到更优 SMT 兄弟，避免短暂激活空闲兄弟造成的持久性能损失。
- [sched-20260903-009](../../2026/09/sched-20260903-009.md) `patch_series/medium/under_review` — `SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。
- [sched-20260903-002](../../2026/09/sched-20260903-002.md) `patch_series/medium/under_review` — steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。v12 相较 09-02 覆盖的 v11 主要做复审吸收与 rebase，并新增对虚拟化场景（paravirt / steal time 记账）的处理：对 vCPU 的 steal time 设上限，使宿主内核在 vCPU 被宿主机偷走时仍能判断「更空闲的 CPU」并迁移任务；同时引入 preferred CPU（结合 misfit / forced idle）以减少跨 LLC 抖动。