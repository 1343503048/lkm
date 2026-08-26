# tag: sched/debug

共 1 篇

- [sched-20260822-007](../../../2026/08/sched-20260822-007-sched-debug-reject-invalid-writes-to-numa-balancing-scan-size-mb.md) `fix/low/under_review` — Lirongqing 的 v2 补丁为 `sched/debug` 增加对 `numa_balancing scan_size_mb` 无效写入的拒绝。v2 改用 `debugfs_create_file_unsafe` 并重写了 commit message。
