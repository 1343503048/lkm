# tag: sched/core

共 4 篇

- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/002 延续。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。
- [sched-20260820-006](../../2026/08/sched-20260820-006.md) `fix/low/under_review` — `struct cpupri_vec` 的 `count` 字段删除从 08-19 的 v1 推进到 08-20 的 v2：RT 优先级队列死代码清理，讨论收敛，合入概率高。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。