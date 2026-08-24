# tag: sched/core

共 8 篇

- [sched-20260823-011](../../2026/08/sched-20260823-011.md) `discussion/medium/under_review` — `sched: Flatten the pick` (v3 0/7) 后续讨论：Peter 让报告者确认 flat_cg 数是基于 flat-hierarchy fix (68e3748781) 还是 single-runqueue (85570f10a4c6)；并提醒 0day 曾 pin 该系列 patch 6/7 导致网络吞吐回退（ksoftirqd 更少运行）。报告者用 0day 复现脚本成功复现回退，分析 `wake_affine_weight()` 在 concur 模式下因 wakee 权重增大而更少选 this_cpu。属 core_sched/proxy_exec 线延续。
- [sched-20260823-004](../../2026/08/sched-20260823-004.md) `fix/medium/under_review` — Dongli Zhang（Oracle）RFC：远程 CPU 更新 rq 时可能在 owner vCPU 仍被 host 抢占期间推进 rq->clock，导致 steal 间隔被错误计入。修复为抢占期间把 delta 累积到 `deferred_clock_task`，待 vCPU 重入时一并折回 irq/steal 记账。RFC 阶段，合入概率 medium。
- [sched-20260823-003](../../2026/08/sched-20260823-003.md) `bug/critical/under_review` — arm64 长运行服务器上偶发 `rq->curr != current`（rq 上记录的当前任务与实际 current 不一致），引发调度器崩溃。生产环境报告，触发条件与内核版本细节待补。属新出现的 crash 报告。
- [sched-20260823-001](../../2026/08/sched-20260823-001.md) `fix/medium/under_review` — Michal Blaszczyk 修一个 CFS/SCX cgroup 参数「三视图发散」竞态：并发写 cpu.shares 等控制文件时，CFS 内部锁在调 SCX 回调前释放，允许多线程穿插，使 CFS 记录值、SCX 簿记、BPF 调度器三者拿到不同参数。v3 把锁上移到 core 层统一串行化。合入概率高。
- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/002 延续。
- [sched-20260820-007](../../2026/08/sched-20260820-007.md) `fix/low/under_review` — `paravirt_steal` 静态键迁移到 `static_branch_*` 的 RESEND 在 08-20 收到 Reviewed-by。这是 08-19 003 系列（调度子系统弃用 raw static_key API）的延续，paravirt 部分此前已获 Juergen Gross Acked-by。
- [sched-20260820-006](../../2026/08/sched-20260820-006.md) `fix/low/under_review` — `struct cpupri_vec` 的 `count` 字段删除从 08-19 的 v1 推进到 08-20 的 v2：RT 优先级队列死代码清理，讨论收敛，合入概率高。
- [sched-20260820-005](../../2026/08/sched-20260820-005.md) `fix/medium/merged_tip` — 两封 sched/urgent 已合入 tip：① `rebuild_sched_domains()` 加 `cpus_read_lock`（对应 08-19 005）；② `tg_cpus()` floor at 1（对应 08-19 001 flat-hierarchy 除零崩溃修复）。tip-bot 8/20 自动应用。