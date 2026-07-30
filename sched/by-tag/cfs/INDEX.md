# tag: cfs

共 6 篇

- [sched-20260729-005](../../2026/07/sched-20260729-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.md) `feature/under_review` — cache-aware 调度系列中的扫描开销优化（`task_cache_work()` 只扫 visited cpus）走到 v8，Tim Chen 给了 Reviewed-by；剩余讨论集中在一个罕见并发场景是否需要显式互斥，Chen Yu 判定可容忍、只需改注释。接近成熟。
- [sched-20260729-004](../../2026/07/sched-20260729-004-sched-core-skip-rq-avg-idle-update-without-a-valid-idle-stam.md) `fix/medium/under_review` — Ampere 的 Shubhang Kaushik 修复 4b603f1551a73 引入的统计缺陷：`update_rq_avg_idle()` 丢失了 `idle_stamp` 有效性检查，`idle_stamp==0` 时会把 `rq_clock(rq)` 整值当 idle 时长，瞬间把 avg_idle 顶到 clamp 上限。已获 Prateek Reviewed-by，合入概率高。
- [sched-20260728-006](../../2026/07/sched-20260728-006-sched-cache-fix-a-thread-aggregation-conflict-when-there-is.md) `fix/medium/under_review` — Zhan Xusheng 发出修复补丁，解决只有一个 runnable task 时的线程聚合冲突。Tim Chen (Intel) 已给出 Reviewed-by，并建议 `SD_ASYM_CPUCAPACITY` 相关代码保持现状。合入可能性高。
- [sched-20260728-005](../../2026/07/sched-20260728-005-sched-cache-reduce-the-overhead-of-task-cache-work-by-only-s.md) `discussion/under_review` — sched/cache 的 task_cache_work 优化补丁（v8）进入深度技术讨论阶段。华为开发者质疑 `visited_cpus` 在扫描期间被并发清除的风险，Chenyu 回复确认 `try_cmpxchg` 已保证同一 mm 同一时刻只有一个 scanner。讨论趋于收敛。
- [sched-20260728-003](../../2026/07/sched-20260728-003-sched-fair-prefer-waker-cpu-for-non-smt-reciprocal-sync-wake.md) `feature/under_review` — Ampere 的 Shubhang Kaushik 发出 v3，针对非 SMT 系统上的 pipe 式 ping-pong 负载，在 wake-affine 域内优先将 wakee 放到 waker CPU 上（而非走 select_idle_sibling 找 idle CPU）。在 80 核 Ampere Altra 上 `perf bench sched pipe` 提升约 30%。v3 刚
- [sched-20260726-001](../../2026/07/sched-20260726-001-sched-make-proxy-execution-compatible-with-sched-ext.md) `feature/under_review` — Andrea Righi 发布的 proxy execution（PE）与 sched_ext 兼容第 9 版（`[PATCHSET v9 sched_ext/for-7.3]`），目标是让 PE 与 sched_ext 共存：当被阻塞任务需要把执行权代理给持锁的 owner，而该 owner 恰好由 SCX 调度器管理时，PE 不能破坏 SCX 的 pick/dispatch 语义。方向已获认可
