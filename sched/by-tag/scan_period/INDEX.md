# tag: scan_period

共 2 篇

- [sched-20260804-013](../../2026/08/sched-20260804-013-sched-numa-fix-scan-period-remote-private-faults.md) `fix/medium/under_review` — Hongling Zeng 的「加速远程私有 fault 扫描周期」补丁被 Zhan Xusheng 精确 review 指出理由不成立（实际未加速），作者承认并发布 v2 改用正确的修正理由。这是「review 抓出错误 commit message」的典型案例，合入可能性 high（v2）。
- [sched-20260804-014](../../2026/08/sched-20260804-014-sched-numa-clear-locality-stats-on-early-return.md) `fix/medium/under_review` — `update_task_scan_period()` 在迁移失败（slow-scan 路径）early return 前未清零 locality 统计，导致同一迁移失败反复选 slow-scan、把扫描周期拖到最大。Hongling Zeng 补上清零，与正常路径一致。Fixes + stable，合入可能性 high。
