# tag: affinity

共 3 篇

- [sched-20260904-002](../../2026/09/sched-20260904-002.md) `patch_series/medium/under_review` — NVIDIA Olympus 以两个对称 PE 实现 SMT：仅一个 PE 活跃时核为单线程模式、可用全部资源；两个 PE 活跃则共享资源。且 sibling 空闲后从双线程回到单线程模式并非即时。本系列（v2，含封面 79146 + 2/2 "Honor asymmetric SMT priority in idle selection"）让空闲 CPU 选择尊重 `SD_ASYM_PACKING`，优先把任务放到更优 SMT 兄弟，避免短暂激活空闲兄弟造成的持久性能损失。
- [sched-20260903-011](../../2026/09/sched-20260903-011.md) `patch_series/medium/under_review` — `migrate_llc_task` 语义用于表达「任务应优先在所属 LLC 域内迁移」。本系列在主动负载均衡（active load balance）路径中尊重该语义，避免把本应限制在 LLC 内的任务错误地推到跨 LLC 的 CPU，减少跨域缓存/内存带宽代价。
- [sched-20260903-009](../../2026/09/sched-20260903-009.md) `patch_series/medium/under_review` — `SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。