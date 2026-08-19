# tag: rt

共 4 篇

- [sched-20260817-003](../../2026/08/sched-20260817-003-scheduler-updates-for-v7-3.md) `feature/high/merged_tip` — Ingo Molnar 发出 v7.3 合并窗口的 **Scheduler updates for v7.3** PR，规模巨大：flatten-the-pick cgroup 调度（扁平权重、运行在 per-CPU 队列而非 cgroup 层级）、EEVDF 核心拆解到单 run queue（CFS 去掉每 cgroup 内部队列）、short-slice 延迟优化、RT 抢占下限、scx 的 
- [sched-20260815-013](../../2026/08/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.md) `regression/high/under_review` — Martin King 报告并修复一个 RT 回归：`CONFIG_NO_RT_PUSH_IPI` 下，当 RT 任务 push 失败（找不到可运行的更低优先级 CPU）时，`rt_rq->rto` 计数未被扣除。残留的 rto 计数让后续 PI-boost 与任务迁移逻辑误判"有 overload"，导致饥饿/迁移停滞。严重度为 high。
- [sched-20260809-005](../../2026/08/sched-20260809-005-kernel-sched-ext-ext-c-1451-38-sparse-sparse-incorrect-type-.md) `fix/low/under_review` — kernel test robot 在 2026-08-09 报告 sched/ext、rt、deadline 子系统的 sparse 警告（地址空间/上下文标注类），并给出修复建议。属代码质量类 fix，合入可能性高。
- [sched-20260804-008](../../2026/08/sched-20260804-008-sched-rt-minor-cleanups.md) `cleanup/low/under_review` — sched/rt 三笔小清理（删未用代码、修翻转注释、其它整洁化），声明无功能影响。低严重度清理，合入可能性 high。
