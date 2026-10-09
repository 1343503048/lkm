# tag: tick

共 4 篇

- [sched-20261007-002](../../2026/10/sched-20261007-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.md) `fix/medium/under_review` — - sched-20261004-002：Stian Halseth 报告 v7.2-rc1 起回归——NO_HZ_IDLE + TICK_CPU_ACCOUNTING 下 `/proc/stat` idle 时间超过墙钟时间（SPARC T7-1 最差 1.44x、KVM guest 1.53x），根因为 cf6444c3e1bb 统一记账后 dyntick-idle 与重启 tick 首个整周
- [sched-20261006-003](../../2026/10/sched-20261006-003-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261005-002](../../2026/10/sched-20261005-002-sched-cputime-don-t-account-idle-time-twice-after-dyntick-id.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261004-002](../../2026/10/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.md) `regression/medium/under_review` — Stian Halseth 报告一个 v7.2-rc1 起的回归：NO_HZ_IDLE + TICK_CPU_ACCOUNTING 内核上 `/proc/stat` 统计的 idle 时间**超过墙钟时间**——按「1 − idle 率」算 CPU 使用率的监控在空闲机器上直接显示负数。两台机器实测（60s 窗口、/proc/stat + /proc/timer_list 的 idle_sleep
