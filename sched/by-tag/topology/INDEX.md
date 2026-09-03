# tag: topology

共 2 篇

- [sched-20260903-009](../../2026/09/sched-20260903-009.md) `patch_series/medium/under_review` — `SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。
- [sched-20260903-002](../../2026/09/sched-20260903-002.md) `patch_series/medium/under_review` — steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。v12 相较 09-02 覆盖的 v11 主要做复审吸收与 rebase，并新增对虚拟化场景（paravirt / steal time 记账）的处理：对 vCPU 的 steal time 设上限，使宿主内核在 vCPU 被宿主机偷走时仍能判断「更空闲的 CPU」并迁移任务；同时引入 preferred CPU（结合 misfit / forced idle）以减少跨 LLC 抖动。