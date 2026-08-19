# tag: regression

共 1 篇

- [sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix](../../2026/08/sched-20260819-001-sched-fair-flat-hierarchy-tgcps-divide-zero-fix.md) `bug/critical/under_review` — tip `sched/core` 的 flat-hierarchy rework 在 enqueue 路径触发 `#DE` 除零 panic（group se 的 `load.weight==0`，`__calc_prop_weight()` 除 `cfs_rq->load.weight`），由 `tg_cpus()` 未对 0 做下限导致；同日配套补丁把 `tg_cpus()` 下限取到 1。critical 级崩溃，但仅影响尚未进主线、由发行版（CachyOS）带入的 tip 系列。