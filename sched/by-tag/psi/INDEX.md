# tag: psi

共 2 篇

- [sched-20260728-008](../../2026/07/sched-20260728-008-sched-psi-fix-32-bit-overflow-in-trigger-window.md) `fix/medium/under_review` — PSI（Pressure Stall Information）trigger 机制在 32 位架构上存在两处整数溢出 bug，导致用户配置的大阈值/窗口（如 4s/6s）被截断为错误值，trigger 监控行为与预期不符。目前 v1 已发出并有社区成员确认问题，等待 maintainer review。
- [sched-20260728-007](../../2026/07/sched-20260728-007-docs-accounting-psi-drop-stale-500ms-window-minimum-from-tri.md) `discussion/low/under_review` — PSI 文档修复补丁的讨论：作者 Tao 计划发 v2，保留 window-range 修复但恢复 system-wide 和 cgroup 文件的统一措辞。此前 commit 8b39d20eceed 已 revert 了 cgroup-specific gating，所以 2s-multiple 规则对两者统一适用。
