# tag: affinity

共 2 篇

- [sched-20260903-011](../../2026/09/sched-20260903-011.md) `patch_series/medium/under_review` — `migrate_llc_task` 语义用于表达「任务应优先在所属 LLC 域内迁移」。本系列在主动负载均衡（active load balance）路径中尊重该语义，避免把本应限制在 LLC 内的任务错误地推到跨 LLC 的 CPU，减少跨域缓存/内存带宽代价。
- [sched-20260903-009](../../2026/09/sched-20260903-009.md) `patch_series/medium/under_review` — `SD_ASYM_PACKING` 会对共享 SMT 核的 CPU 排序，但空闲 CPU 选择（wakeup idle selection）并不参考该顺序，任务可落到任意兄弟线程并停留到负载均衡纠正。在「切换活跃兄弟会重新划分核资源」的 SMT 实现上，初始选择会造成巨大且持续的性能损失。