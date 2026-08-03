# tag: sched_clock

共 2 篇

- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical，合入基本无悬念。
- [sched-20260802-005](../../2026/08/sched-20260802-005-nohz-replace-dead-select-with-choice-default.md) `fix/low/under_review` — Kconfig 中 `select` 对 `choice` 内的选项无效，`NO_HZ_FULL` 里的 `select VIRT_CPU_ACCOUNTING_GEN` 是一行死代码。补丁删除它并改用 choice 的条件 default 表达同一关系。由静态分析工具 kconfirm 发现，已获一个非维护者的 Reviewed-by，但缺少配置验证数据且无维护者关注，存在沉寂风险。
