# tag: tick

共 1 篇

- [sched-20261004-002](../../2026/10/sched-20261004-002-tick-sched-proc-stat-idle-time-exceeds-wall-time-since-v7-2.md) `regression/medium/under_review` — Stian Halseth 报告一个 v7.2-rc1 起的回归：NO_HZ_IDLE + TICK_CPU_ACCOUNTING 内核上 `/proc/stat` 统计的 idle 时间**超过墙钟时间**——按「1 − idle 率」算 CPU 使用率的监控在空闲机器上直接显示负数。两台机器实测（60s 窗口、/proc/stat + /proc/timer_list 的 idle_sleep
