# tag: sched_debug

共 1 篇

- [sched-20260905-002](../../2026/09/sched-20260905-002.md) `fix/high/under_review` — `scan_size_mb` 在 `task_scan_max()` 中作为除数使用，而 `debugfs_create_u32()` 对写入值不做校验。向 `/sys/kernel/debug/sched/numa_balancing/scan_size_mb` 写入 0（或某些值）会在 `task_scan_max+0x30` 触发 "divide error" Oops，调用链 `init_numa_balancing → __sched_fork → sched_fork`，导致内核 panic。本补丁（v2 RESEND）对写入做合法性校验。