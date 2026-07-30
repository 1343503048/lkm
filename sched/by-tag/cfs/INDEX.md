# tag: cfs

共 3 篇

- [sched-20260729-005](../../2026/07/sched-20260729-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.md) `feature/under_review` — cache-aware 调度系列中的扫描开销优化（`task_cache_work()` 只扫 visited cpus）走到 v8，Tim Chen 给了 Reviewed-by；剩余讨论集中在一个罕见并发场景是否需要显式互斥，Chen Yu 判定可容忍、只需改注释。接近成熟。
- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260726-001](../../2026/07/sched-20260726-001-sched-make-proxy-execution-compatible-with-sched-ext.md) `feature/under_review` — Andrea Righi 发布的 proxy execution（PE）与 sched_ext 兼容第 9 版（`[PATCHSET v9 sched_ext/for-7.3]`），目标是让 PE 与 sched_ext 共存：当被阻塞任务需要把执行权代理给持锁的 owner，而该 owner 恰好由 SCX 调度器管理时，PE 不能破坏 SCX 的 pick/dispatch 语义。方向已获认可
