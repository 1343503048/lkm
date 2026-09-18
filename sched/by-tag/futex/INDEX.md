# tag: futex

共 2 篇

- [sched-20260918-011](../../2026/09/sched-20260918-011-futex-ping-a-stealable-futex-using-proxy-execution.md) `feature/rfc` — 增量更新：Suleiman Souhlal 的 FUTEX_PING（可偷取 futex + Proxy Execution，RFC 00/12）本日迎来密集高层讨论。Steven Rostedt 与 John Stultz 回溯了 FUTEX_PI 强制公平导致 SCHED_OTHER 性能崩溃、催生新 futex 的动机；Peter Zijlstra 指出"又想要 Priority Inher
- [sched-20260821-009](../../2026/08/sched-20260821-009-futex-fix-might-sleep-warning-in-futex-pivot-pending.md) `fix/medium/merged_tip` — PeterZ 修复 `futex_pivot_pending()` 中的 `might_sleep()` 告警，已合入 `tip: locking/urgent` 分支。commit `d8aa5dd97944`。
