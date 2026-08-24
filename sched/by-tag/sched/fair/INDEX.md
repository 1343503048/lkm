# tag: sched/fair

共 13 篇

- [sched-20260824-011-sched-fair-reuse-enqueue-delayed](../../2026/08/sched-20260824-011-sched-fair-reuse-enqueue-delayed.md) `fix/low/under_review` — EEVDF 路径中，实体入队（enqueue）时涉及 `ENQUEUE_DELAYED` 标志与 `curr` 状态
- [sched-20260824-009-sched-flatten-the-pick](../../2026/08/sched-20260824-009-sched-flatten-the-pick.md) `discussion/medium/discussion` — “Flatten the pick”是一轮关于把调度器选核（pick）路径从多层嵌套调用扁平化、
- [sched-20260824-006-sched-fair-null-deref-v4.19](../../2026/08/sched-20260824-006-sched-fair-null-deref-v4.19.md) `bug/high/under_review` — 在基于 v4.19 的厂商内核上，`pick_next_task_fair()` 中触发了空指针解引用
- [sched-20260824-004-sched-fair-cpufreq-pressure-invariant](../../2026/08/sched-20260824-004-sched-fair-cpufreq-pressure-invariant.md) `fix/medium/under_review` — cpufreq 压力（cpufreq pressure）用于向调度器反馈由于频率受限带来的算力损失。
- [sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle](../../2026/08/sched-20260824-002-sched-cpufreq-reevaluate-tickless-idle.md) `fix/medium/under_review` — 在进入 tickless idle（NOHZ idle）之前，调度器与 cpufreq 之间的协调存在窗口：
- [sched-20260823-009](../../2026/08/sched-20260823-009.md) `fix/low/under_review` — `sched/fair: Only apply cpufreq pressure where frequency is invariant` 的讨论继续：cpufreq pressure 按「可达最高频率/当前可达最高频率」降 capacity，但 utilization 仅在频率不变架构才带匹配 scaling，导致语义不一致。焦点在「是否仅在不 invariant 场景施加 pressure」。合入概率 medium。
- [sched-20260823-002](../../2026/08/sched-20260823-002.md) `bug/high/under_review` — 两个生产环境（aarch64 Kunpeng 920、vendor 4.19.90）在长 uptime 后各自崩溃于 `pick_next_task_fair()` 解引用 NULL：root cfs_rq 的 `nr_running` 被污染成 0xFFFFFFFF（-1），使 idle 判定失效、从空 rb 树取到 NULL。签名一致，疑似 nr_running 计数损坏。基于 vendor 4.19，是否主线程可复现待定。
- [sched-20260820-010](../../2026/08/sched-20260820-010.md) `bug/critical/under_review` — flat-hierarchy 除零崩溃（08-19 001）的 08-20 诊断更新：报告者打开 CONFIG_DEBUG 后 diagnosis WARN 确实触发，确认根因走 cpuset 路径（非仅发行版），uptime 21.4h 复现。配套 fix（tg_cpus floor at 1）已合入 tip（见 08-20 005）。
- [sched-20260820-009](../../2026/08/sched-20260820-009.md) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」，以保留空闲 SMT 兄弟供单线程突发。属 08-09 009 线的延续。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。
- [sched-20260820-004](../../2026/08/sched-20260820-004.md) `bug/low/under_review` — LKP sparse 在 `kernel/sched/fair.c:2004`（enqueue 路径判断 `cfs_rq->nr_running`）发出静态检查告警，疑似近期 commit `85570f10a4c6`（EEVDF single runqueue 合并）引入。无修复补丁，仅自动报告。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。