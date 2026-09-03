# tag: load_balance

共 4 篇

- [sched-20260903-012](../../2026/09/sched-20260903-012.md) `patch_series/medium/rfc` — 作为 NUMA 细粒度均衡 + `sched/cache` 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。
- [sched-20260903-011](../../2026/09/sched-20260903-011.md) `patch_series/medium/under_review` — `migrate_llc_task` 语义用于表达「任务应优先在所属 LLC 域内迁移」。本系列在主动负载均衡（active load balance）路径中尊重该语义，避免把本应限制在 LLC 内的任务错误地推到跨 LLC 的 CPU，减少跨域缓存/内存带宽代价。
- [sched-20260902-015-sched-remove-sched-class-balance](../../2026/09/sched-20260902-015-sched-remove-sched-class-balance.md) `fix/low/under_review` — 调度类（sched_class）的 `balance()` 回调历史上用于某个调度类的负载均衡钩子，但现代
- [sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers](../../2026/09/sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers.md) `feature/medium/under_review` — 这是一个较大的 RFC 系列（v2，共 23 个补丁），方向是 **NUMA 细粒度均衡** 与