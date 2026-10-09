# tag: amd_pstate

共 1 篇

- [sched-20261002-006](../../2026/10/sched-20261002-006-cpufreq-amd-pstate-restore-previous-mode-when-changing-drive.md) `fix/low/under_review` — Mario Limonciello（AMD，amd-pstate 维护者）的 3 补丁 v2（前身 09-21 的 4 补丁 v1，v1 未在既往分析窗口覆盖）：修复 amd-pstate 模式切换的两个健壮性缺口与 Zen6 上两个单元测试失败。1/3：`amd_pstate_change_driver_mode()` 注册新模式失败后什么也不恢复、系统失去 scaling driver，改为记
