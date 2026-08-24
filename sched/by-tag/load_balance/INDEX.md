# tag: load_balance

共 4 篇

- [sched-20260823-011](../../2026/08/sched-20260823-011.md) `discussion/medium/under_review` — `sched: Flatten the pick` (v3 0/7) 后续讨论：Peter 让报告者确认 flat_cg 数是基于 flat-hierarchy fix (68e3748781) 还是 single-runqueue (85570f10a4c6)；并提醒 0day 曾 pin 该系列 patch 6/7 导致网络吞吐回退（ksoftirqd 更少运行）。报告者用 0day 复现脚本成功复现回退，分析 `wake_affine_weight()` 在 concur 模式下因 wakee 权重增大而更少选 this_cpu。属 core_sched/proxy_exec 线延续。
- [sched-20260823-010](../../2026/08/sched-20260823-010.md) `fix/medium/under_review` — `sched/cache: honor migrate_llc_task semantics in active load balance` v3 已获 Tim Chen、Chen Yu 的 Reviewed-by，8/23 为 gentle ping 请 Peter 收下。核心是 active load balance 的迁移类型遵循 `migrate_llc_task` 语义，避免影响 delayed-dequeue 任务的 `migration_type` 含义。合入概率 high。
- [sched-20260820-011](../../2026/08/sched-20260820-011.md) `discussion/medium/under_review` — `Remove sched_class::balance()` 系列与 core_sched pick_task 竞态在 08-20 继续交织：Peter 给出 core_seq 跟踪多 pick 的 sketch、Tejun 确认 SCX 下锁丢弃可前进、idle pick 传 NULL rf。forward-progress（活锁）保证仍未敲定，原始 cover 仍缺。属 08-19 011/002 延续。
- [sched-20260820-009](../../2026/08/sched-20260820-009.md) `fix/low/under_review` — Andrea Righi 的 NOHZ idle 平衡系列推进到 v4：优先把任务搬到「完全空闲核心」而非「仅部分兄弟线程空闲的核心」，以保留空闲 SMT 兄弟供单线程突发。属 08-09 009 线的延续。