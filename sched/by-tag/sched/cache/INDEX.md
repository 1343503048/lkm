# tag: sched/cache

共 2 篇

- [sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers](../../2026/09/sched-20260902-009-rfc-v2-numa-fine-balance-sched-cache-helpers.md) `feature/medium/under_review` — 这是一个较大的 RFC 系列（v2，共 23 个补丁），方向是 **NUMA 细粒度均衡** 与
- [sched-20260902-003-sched-cache-uaf-mm-access](../../2026/09/sched-20260902-003-sched-cache-uaf-mm-access.md) `bug/high/under_review` — `sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务