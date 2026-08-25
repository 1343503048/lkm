# tag: rt

共 8 篇

- [sched-20260820-006](../../2026/08/sched-20260820-006.md) `fix/low/under_review` — `struct cpupri_vec` 的 `count` 字段删除从 08-19 的 v1 推进到 08-20 的 v2：RT 优先级队列死代码清理，讨论收敛，合入概率高。
- [sched-20260820-001](../../2026/08/sched-20260820-001.md) `fix/medium/under_review` — Zhe Liu 修一个 CFS 带宽配置顺序陷阱：先 `cpu.max.burst` 配大值、再设有限 `cpu.max` quota 时，因旧 burst 校验不通过导致 quota 写入直接 EINVAL。修复为「改 quota 不兼容则把 burst 清零」，附文档与 selftest。Michal Koutny 倾向改成 clamp 到 quota，分歧待解。
- [sched-20260819-006](../../2026/08/sched-20260819-006-sched-rt-cpupri-remove-count-field.md) `fix/low/under_review` — 从 RT 优先级队列 `struct cpupri_vec` 中删除未使用的 `count` 字段，纯死代码清理。
- [sched-20260819-005](../../2026/08/sched-20260819-005-sched-topology-cpus-read-lock-rebuild-sched-domains.md) `fix/medium/under_review` — Sebastian Siewior 修复 `CONFIG_CPUSETS=n` 下读 `sched_rt_runtime_us` 因缺 `cpu_hotplug_lock` 触发的 backtrace，v2 把 `cpus_read_lock` 上移到 `rebuild_sched_domains()`。同时顺带修好 EAS 在 CPUfreq governor 切换时的同类问题。
- [sched-20260817-003](../../2026/08/sched-20260817-003-scheduler-updates-for-v7-3.md) `feature/high/merged_tip` — Ingo Molnar 发出 v7.3 合并窗口的 **Scheduler updates for v7.3** PR，规模巨大：flatten-the-pick cgroup 调度（扁平权重、运行在 per-CPU 队列而非 cgroup 层级）、EEVDF 核心拆解到单 run queue（CFS 去掉每 cgroup 内部队列）、short-slice 延迟优化、RT 抢占下限、scx 的 
- [sched-20260815-013](../../2026/08/sched-20260815-013-sched-rt-no-rt-push-ipi-causes-multi-second-pi-boost-starvat.md) `regression/high/under_review` — Martin King 报告并修复一个 RT 回归：`CONFIG_NO_RT_PUSH_IPI` 下，当 RT 任务 push 失败（找不到可运行的更低优先级 CPU）时，`rt_rq->rto` 计数未被扣除。残留的 rto 计数让后续 PI-boost 与任务迁移逻辑误判"有 overload"，导致饥饿/迁移停滞。严重度为 high。
- [sched-20260809-005](../../2026/08/sched-20260809-005-kernel-sched-ext-ext-c-1451-38-sparse-sparse-incorrect-type-.md) `fix/low/under_review` — kernel test robot 在 2026-08-09 报告 sched/ext、rt、deadline 子系统的 sparse 警告（地址空间/上下文标注类），并给出修复建议。属代码质量类 fix，合入可能性高。
- [sched-20260804-008](../../2026/08/sched-20260804-008-sched-rt-minor-cleanups.md) `cleanup/low/under_review` — sched/rt 三笔小清理（删未用代码、修翻转注释、其它整洁化），声明无功能影响。低严重度清理，合入可能性 high。
