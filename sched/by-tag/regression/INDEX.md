# tag: regression

共 2 篇

- [sched-20260903-006](../../2026/09/sched-20260903-006.md) `regression/high/under_review` — 提交 `dd29c017aed6`（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）在非 PREEMPT_RT 桌面引入可复现的多秒级音频掉帧。报告人 Martin King 在 DAW（数字音频工作站）场景中观察到 PI-boost 饥饿。Steven Rostedt 于 09-03 就该回归发信询问进展，已纳入 tracked regression。
- [sched-20260902-008-sched-fair-cpufreq-pressure-invariant](../../2026/09/sched-20260902-008-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-24/08-25 的文章）