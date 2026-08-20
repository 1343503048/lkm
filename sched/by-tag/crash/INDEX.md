# tag: crash

共 2 篇

- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。