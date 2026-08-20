# tag: sched/fair

共 6 篇

- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-009](../../2026/08/sched-20260820-009.md) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」，以保留空闲 SMT 兄弟供单线程突发。属 08-09 009 线的延续。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。
- [sched-20260820-004](../../2026/08/sched-20260820-004.md) `bug/low/under_review` — LKP sparse 在 `kernel/sched/fair.c:2004`（enqueue 路径判断 `cfs_rq->nr_running`）发出静态检查告警，疑似近期 commit `85570f10a4c6`（EEVDF single runqueue 合并）引入。无修复补丁，仅自动报告。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。