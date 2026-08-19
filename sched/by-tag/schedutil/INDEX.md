# tag: schedutil

共 2 篇

- [sched-20260816-004](../../2026/08/sched-20260816-004.md) `fix/medium/merged_tip` — Hui Su 的 v3（延续 08-07 系列 006）修复 `schedutil` 在 32 位平台的频率限制溢出：`rate_limit_us`（unsigned int）乘 `NSEC_PER_USEC`(1000L) 在 32 位下以 32 位无符号算术进行，写大值（如 4294968）会让 `freq_update_delay_ns` 从 4294968000ns 溢出为 704ns，使
- [sched-20260807-003-schedutil-boost-dvfs-policy-max.md](../../2026/08/sched-20260807-003-schedutil-boost-dvfs-policy-max.md) `in-review`
