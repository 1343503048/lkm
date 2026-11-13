# tag: membarrier

共 2 篇

- [sched-20261113-004](../../2026/11/sched-20261113-004-sched-membarrier-report-only-completed-registrations.md) `bug/medium/rfc` — Mathieu Desnoyers 的 RFC 系列（16 补丁）修复之二：`MEMBARRIER_CMD_GET_REGISTRATIONS` 目前只要注册的任一状态位置位就上报，导致只注册了 sync core 或 rseq 的进程被误报为也注册了 `PRIVATE_EXPEDITED`（进而 `MEMBARRIER_CMD_PRIVATE_EXPEDITED` 返回 -EPERM），-ENO
- [sched-20261113-003](../../2026/11/sched-20261113-003-sched-membarrier-fix-stale-runqueue-state-after-a-lazy-mm-sw.md) `bug/critical/rfc` — Mathieu Desnoyers（membarrier 机制作者）发 RFC 系列（16 补丁）的修复之一：`MEMBARRIER_CMD_GLOBAL_EXPEDITED` 依赖 `rq->membarrier_state` 定位要发 IPI 的 CPU，但 `membarrier_switch_mm()` 用 `prev->active_mm` 与 `next->mm` 比较，导致 lazy
