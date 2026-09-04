# tag: crash

共 4 篇

- [sched-20260904-011](../../2026/09/sched-20260904-011.md) `patch_series/high/under_review` — 延续 09-03 004，sub-sched 错误路径 NULL deref 修复进入 v3，本日收到复审（Re）。错误路径（open/enable 失败回滚）访问已释放/未初始化的 `sched` 对象，可能触发 NULL deref crash。
- [sched-20260903-004](../../2026/09/sched-20260903-004.md) `patch_series/high/under_review` — 在 sub-sched（子调度）的错误处理路径（open/enable 失败回滚）中，访问了已释放/未初始化的 `sched` 对象，导致 NULL 解引用，可能触发 NULL deref crash。本系列覆盖两类触发点：`kfunc` 子调度错误路径与 `select_cpu_and` 子调度错误路径。
- [sched-20260902-006-sched-ext-null-deref-select-cpu-and](../../2026/09/sched-20260902-006-sched-ext-null-deref-select-cpu-and.md) `bug/high/under_review` — `sched_ext` 在 `select_cpu_and` 处理「子调度（sub-sched）」错误路径时，未对 `sched`
- [sched-20260902-003-sched-cache-uaf-mm-access](../../2026/09/sched-20260902-003-sched-cache-uaf-mm-access.md) `bug/high/under_review` — `sched/cache` 的 `account_mm_sched()` 在统计缓存亲和时，会访问任务的 `mm`。当任务