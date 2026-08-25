# tag: sched/fair

共 5 篇

- [sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq](../../2026/08/sched-20260825-011-sched-fair-update-curr-eevdf-root-cfs-rq.md) `fix/low/discussion` — EEVDF 路径中，仍有部分直接操作 `root cfs_rq` 的调用点未统一走 `update_curr_eevdf()`
- [sched-20260825-009-question-combine-detach-dequeue-guest-hang](../../2026/08/sched-20260825-009-question-combine-detach-dequeue-guest-hang.md) `bug/high/under_review` — 报告者（UID 57212 / 57225 / 57402）反馈：在开启用户态限流（userspace throttling，
- [sched-20260825-008-sched-steal-governor-v11](../../2026/08/sched-20260825-008-sched-steal-governor-v11.md) `feature/medium/under_review` — steal_governor 系列（v11，UID 57064 00/12 等共 12 个补丁）引入「preferred CPUs」
- [sched-20260825-006-sched-fair-cpufreq-pressure-invariant](../../2026/08/sched-20260825-006-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24 的文章）
- [sched-20260825-005-sched-cpufreq-reevaluate-tickless-idle](../../2026/08/sched-20260825-005-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24 的文章）