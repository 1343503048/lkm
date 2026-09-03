# tag: sched/cache

共 6 篇

- [sched-20260903-012](../../2026/09/sched-20260903-012.md) `patch_series/medium/rfc` — 作为 NUMA 细粒度均衡 + `sched/cache` 辅助框架的一部分，本系列（RFC v2，共 23 个 patch 中的 11/23）引入一组任务迁移决策辅助函数，把「是否跨 LLC / 跨 NUMA 迁移、迁移到哪个层级」的判断集中到可复用的 helper，供负载均衡、NUMA 平衡、steal 等多处复用。
- [sched-20260903-011](../../2026/09/sched-20260903-011.md) `patch_series/medium/under_review` — `migrate_llc_task` 语义用于表达「任务应优先在所属 LLC 域内迁移」。本系列在主动负载均衡（active load balance）路径中尊重该语义，避免把本应限制在 LLC 内的任务错误地推到跨 LLC 的 CPU，减少跨域缓存/内存带宽代价。
- [sched-20260903-002](../../2026/09/sched-20260903-002.md) `patch_series/medium/under_review` — steal_governor 让过载 CPU 从空闲/轻载 CPU「窃取」任务，以缓解大机/SMT 拓扑下的核间负载不均。v12 相较 09-02 覆盖的 v11 主要做复审吸收与 rebase，并新增对虚拟化场景（paravirt / steal time 记账）的处理：对 vCPU 的 steal time 设上限，使宿主内核在 vCPU 被宿主机偷走时仍能判断「更空闲的 CPU」并迁移任务；同时引入 preferred CPU（结合 misfit / forced idle）以减少跨 LLC 抖动。
- [sched-20260903-001](../../2026/09/sched-20260903-001.md) `patch_series/medium/under_review` — 代理执行（proxy execution）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）分离。周期性 tick 中仍有部分记账/扫描以 donor 触发，导致 NUMA 周期扫描、`cache` 任务 tick、以及 workqueue 的 `wq_worker_tick()` 都基于「`sum_exec_runtime` 未被代理执行推进」的 donor 任务，造成 NUMA 扫描错位、cache tick 错配与 kworker 记账丢失。本系列把这几类周期行为改到基于 `rq->curr` 的真实执行上下文。
- [sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers](../../2026/09/sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers.md) `feature/medium/under_review` — 这是一个较大的 RFC 系列（v2，共 23 个补丁），方向是 **NUMA 细粒度均衡** 与
- [sched-20260902-003-sched-cache-uaf-mm-access](../../2026/09/sched-20260902-003-sched-cache-uaf-mm-access.md) `bug/high/under_review` — `sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务