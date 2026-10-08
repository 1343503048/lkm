# tag: autogroup

共 1 篇

- [sched-20261008-003](../../2026/10/sched-20261008-003-sched-autogroup-serialize-nice-rate-limit-updates.md) `fix/low/under_review` — Hui Su 修掉 `proc_sched_autogroup_set_nice()` 里一个经典的 check-then-act 竞态：用函数级静态时间戳做 100ms 限流的检查和更新不是原子的，两个并发非特权写者可同时看到过期时间戳、都进入 `sched_group_set_shares()`，击穿限流。补丁用一个专用 spinlock 串行化时间戳的查/改，能力检查移出临界区、重活保持锁外
