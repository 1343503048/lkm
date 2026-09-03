# tag: proxy_execution

共 4 篇

- [sched-20260903-008](../../2026/09/sched-20260903-008.md) `patch_series/medium/under_review` — 代理执行分离调度上下文与执行上下文。调度器运行时间记账将 cgroup 时间记到 donor，而 tick 与 vtime 记账在更新 cgroup 字段时却使用执行任务。当 donor 与执行任务分属不同 cgroup 时，会把 donor cgroup 的 `cpu.stat` usage 记给 donor，而 user/system 字段记给执行任务 cgroup，造成统计错乱（donor cgroup 凭空获得 usage 时间，执行 cgroup 获得 system 时间）。
- [sched-20260903-005](../../2026/09/sched-20260903-005.md) `patch_series/high/under_review` — 代理执行下 `task_tick_rt()` 针对调度上下文 `rq->donor` 调用，而 `rq->curr` 才是真正执行任务。RT watchdog 通过 `task` 参数查 `RLIMIT_RTTIME` 并更新该任务的 `rt.timeout` 与 `posix_cputimers` 状态；但运行时间记账记到 `rq->curr`，`run_posix_cpu_timers()` 检查 `current`。若不传 `rq->curr`，watchdog 状态更新会跟随错误的（donor）上下文，导致 `RLIMIT_RTTIME` 误触发/漏触发与 posix 定时器状态错乱。
- [sched-20260903-001](../../2026/09/sched-20260903-001.md) `patch_series/medium/under_review` — 代理执行（proxy execution）把调度上下文（`rq->donor`）与执行上下文（`rq->curr`）分离。周期性 tick 中仍有部分记账/扫描以 donor 触发，导致 NUMA 周期扫描、`cache` 任务 tick、以及 workqueue 的 `wq_worker_tick()` 都基于「`sum_exec_runtime` 未被代理执行推进」的 donor 任务，造成 NUMA 扫描错位、cache tick 错配与 kworker 记账丢失。本系列把这几类周期行为改到基于 `rq->curr` 的真实执行上下文。
- [sched-20260902-001-proxy-execution-batch-merge](../../2026/09/sched-20260902-001-proxy-execution-batch-merge.md) `feature/medium/merged_tip` — Proxy Execution（PE，解决优先级翻转 / 锁持有者代理运行）在 09-02 有一批改动合入