# tag: autogroup

共 5 篇

- [sched-20261030-008](../../2026/10/sched-20261030-008-sched-autogroup-fix-task-group-uaf-during-thread-creation.md) `fix/critical/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261026-003](../../2026/10/sched-20261026-003-sched-autogroup-fix-task-group-uaf-during-thread-creation.md) `fix/critical/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261023-004](../../2026/10/sched-20261023-004-sched-autogroup-fix-task-group-uaf-during-thread-creation.md) `fix/critical/under_review` — Daehyeon Ko 发往 sched 的单补丁修复一个 autogroup 的 use-after-free：`sched_cgroup_fork()` 在 CLONE_THREAD 子进程尚未挂上线程链表前就把它指到 `p->signal->autogroup->tg`，而 autogroup 归属是 per-`signal_struct`、CLONE_THREAD 复用旧 `signal_
- [sched-20261012-017](../../2026/10/sched-20261012-017-sched-autogroup-make-nice-rate-limit-updates-atomic.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261008-003](../../2026/10/sched-20261008-003-sched-autogroup-serialize-nice-rate-limit-updates.md) `fix/low/under_review` — Hui Su 修掉 `proc_sched_autogroup_set_nice()` 里一个经典的 check-then-act 竞态：用函数级静态时间戳做 100ms 限流的检查和更新不是原子的，两个并发非特权写者可同时看到过期时间戳、都进入 `sched_group_set_shares()`，击穿限流。补丁用一个专用 spinlock 串行化时间戳的查/改，能力检查移出临界区、重活保持锁外
