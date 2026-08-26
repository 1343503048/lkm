# tag: sched/fair

共 6 篇

- [sched-20260826-009-sched-fair-reduce-repeated-work-enqueue-v2](../../2026/08/sched-20260826-009-sched-fair-reduce-repeated-work-enqueue-v2.md) `fix/low/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）
- [sched-20260826-008-question-combine-detach-dequeue-guest-hang](../../2026/08/sched-20260826-008-question-combine-detach-dequeue-guest-hang.md) `bug/high/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-25 的文章）
- [sched-20260826-006-sched-fair-reset-incompatible-burst-quota-change](../../2026/08/sched-20260826-006-sched-fair-reset-incompatible-burst-quota-change.md) `fix/low/under_review` — CFS 带宽控制（cpu.cfs_quota_us / cpu.cfs_period_us / cpu.cfs_burst_us）中，当任务的
- [sched-20260826-005-sched-fair-restart-hrtick-same-task-repicks](../../2026/08/sched-20260826-005-sched-fair-restart-hrtick-same-task-repicks.md) `fix/low/under_review` — 在 `sched/fair` 中，当发生「同一任务重新选核/重新入队（same-task repicks）」时，
- [sched-20260826-003-sched-cpufreq-reevaluate-tickless-idle](../../2026/08/sched-20260826-003-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）
- [sched-20260826-002-sched-fair-avoid-misfits-cache-aware-balancing](../../2026/08/sched-20260826-002-sched-fair-avoid-misfits-cache-aware-balancing.md) `fix/medium/under_review` — cache-aware scheduling（考虑 LLC/缓存域的负载均衡）在选核与迁移时，可能把任务放到