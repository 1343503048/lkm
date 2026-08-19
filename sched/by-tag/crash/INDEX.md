# tag: crash

共 2 篇

- [sched-20260819-002-core-sched-pick-task-race-null-deref-discussion](../../2026/08/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.md) `discussion/high/under_review` — core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续，造成 `rqX->core_pick` 被对端置 NULL 后空指针解引用。Peter 8/19 回复承认这是个漂亮竞态，但尚无好修复，且 sched_ext 参与让问题更复杂。属于 08-17→08-18 core_sched/proxy_exec 讨论线的延续。
- [sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix](../../2026/08/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.md) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group se 的 `load.weight==0`，`__calc_prop_weight()` 除 `cfs_rq->load.weight`），由 `tg_cpus()` 未对 0 做下限导致；同日配套补丁把 `tg_cpus()` 下限取到 1。critical 级崩溃，但仅影响尚未进主线、由发行版（CachyOS）带入的 tip 系列。