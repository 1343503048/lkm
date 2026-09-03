# tag: crash

共 2 篇

- [sched-20260902-006-sched-ext-null-deref-select-cpu-and](../../2026/09/sched-20260902-006-sched-ext-null-deref-select-cpu-and.md) `bug/high/under_review` — `sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
- [sched-20260902-003-sched-cache-uaf-mm-access](../../2026/09/sched-20260902-003-sched-cache-uaf-mm-access.md) `bug/high/under_review` — `sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务