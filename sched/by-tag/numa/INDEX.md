# tag: numa

共 8 篇

- [sched-20260817-005](../../2026/08/sched-20260817-005-sched-steal-governor-introduce-preferred-cpus-and-steal-driv.md) `feature/medium/under_review` — `steal_governor` v10 的讨论回复（Shrikanth Hegde，接 Prateek/K Prateek/J Joel 等 review）：系列引入"preferred CPUs"与"steal-driven vCPU backoff"，让空闲/轻载 CPU 从忙 CPU 偷取任务以减少空闲时间。本日回复集中回应三处缺陷——① 32 位 ARM64 上 `atomic_long
- [sched-20260806-014](../../2026/08/sched-20260806-014-sched-numa-hygon-remote-socket-distance-v2.md) `fix/medium/under_review`
- [sched-20260804-015](../../2026/08/sched-20260804-015-sched-numa-prevent-race-sysctl-static-key-v2.md) `bug/high/under_review` — `sysctl_numa_balancing` 静态键切换竞态（UAF/use-after-uninit，附 syzkaller repro + Fixes）在 08-04 继续推进。这是 08-03-006 的延续，合入可能性 high。
- [sched-20260804-014](../../2026/08/sched-20260804-014-sched-numa-clear-locality-stats-on-early-return.md) `fix/medium/under_review` — `update_task_scan_period()` 在迁移失败（slow-scan 路径）early return 前未清零 locality 统计，导致同一迁移失败反复选 slow-scan、把扫描周期拖到最大。Hongling Zeng 补上清零，与正常路径一致。Fixes + stable，合入可能性 high。
- [sched-20260804-013](../../2026/08/sched-20260804-013-sched-numa-fix-scan-period-remote-private-faults.md) `fix/medium/under_review` — Hongling Zeng 的「加速远程私有 fault 扫描周期」补丁被 Zhan Xusheng 精确 review 指出理由不成立（实际未加速），作者承认并发布 v2 改用正确的修正理由。这是「review 抓出错误 commit message」的典型案例，合入可能性 high（v2）。
- [sched-20260804-012](../../2026/08/sched-20260804-012-sched-topology-free-numa-masks-on-alloc-failure.md) `fix/low/under_review` — `sched_domains_numa_masks` 在部分分配失败时未释放已分配掩码，存在错误路径泄漏。Hongling Zeng 补上清理。低严重度清理，属 medium（需确认与其它 topology 清理的合并）。
- [sched-20260803-009](../../2026/08/sched-20260803-009-sched-numa-apply-remote-socket-distance-averaging-for-hygon-7447v.md) `feature/under_review` — `sched/numa` 针对 Hygon 7447V 的模块化布局，把远程 socket 节点距离取平均以区分 intra/inter-socket 远程代价。已获 Ingo Acked-by，合入可能性高。
- [sched-20260803-006](../../2026/08/sched-20260803-006-sched-numa-prevent-race-on-sysctl_numa_balancing-static-key.md) `bug/high/under_review` — `sched/numa` 修复 `sysctl_numa_balancing` 静态键切换时的抢占竞态（UAF / use-after-uninit），附 syzkaller C repro 与 Fixes 标签。问题真实且有复现，合入可能性高。
