# tag: rt

共 3 篇

- [sched-20260906-004](../../2026/09/sched-20260906-004.md) `discussion/none/merged_tip` — Ingo 向 Linus 发出 sched/urgent 修复拉取（顶端 `f0d243a96f26`），含 3 个调度修复：fair 类时间戳 bug、RT/DL push 候选跳过 migrate-disabled 任务、avg_idle 在无 idle_stamp 时跳过更新。属紧急修复，已基本合入主线。
- [sched-20260903-006](../../2026/09/sched-20260903-006.md) `regression/high/under_review` — 提交 `dd29c017aed6`（"sched/rt: Have RT_PUSH_IPI be default off for non PREEMPT_RT"）在非 PREEMPT_RT 桌面引入可复现的多秒级音频掉帧。报告人 Martin King 在 DAW（数字音频工作站）场景中观察到 PI-boost 饥饿。Steven Rostedt 于 09-03 就该回归发信询问进展，已纳入 tracked regression。
- [sched-20260903-005](../../2026/09/sched-20260903-005.md) `patch_series/high/under_review` — 代理执行下 `task_tick_rt()` 针对调度上下文 `rq->donor` 调用，而 `rq->curr` 才是真正执行任务。RT watchdog 通过 `task` 参数查 `RLIMIT_RTTIME` 并更新该任务的 `rt.timeout` 与 `posix_cputimers` 状态；但运行时间记账记到 `rq->curr`，`run_posix_cpu_timers()` 检查 `current`。若不传 `rq->curr`，watchdog 状态更新会跟随错误的（donor）上下文，导致 `RLIMIT_RTTIME` 误触发/漏触发与 posix 定时器状态错乱。