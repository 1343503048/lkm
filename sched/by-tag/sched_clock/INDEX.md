# tag: sched_clock

共 5 篇

- [sched-20260906-005](../../2026/09/sched-20260906-005-sched-clock-add-option-to-use-absolute-time-against-hardware-clock-reset.md) `discussion/stalled` — 本文为 09-03 第 015 篇（sched_clock 绝对时间选项）的增量更新：Thomas Gleixner 明确 NAK，称其是 firmware debug hack，维护者不关心这类 bug-chasing 故事。系列基本停滞，不建议继续跟进。
- [sched-20260903-015](../../2026/09/sched-20260903-015-sched-clock-add-option-to-use-absolute-time-against-hardware-clock-reset.md) `discussion/medium/under_review` — 部分平台的硬件时钟会在复位/暂停后回绕或清零，使基于它的 sched_clock() 出现跳变，影响调度时间基准与 trace 一致性。目前本日有多封复审（Re）讨论复位检测与补偿语义、对不同平台的影响。- 与 sched-20260902-013 同系列，仍在讨论收敛中。
- [sched-20260826-009](../../2026/08/sched-20260826-009-sched-fair-restart-hrtick-after-same-task-repicks.md) `fix/low/under_review` — Shubhang Kaushik (Ampere) 提交补丁修复 same-task repick 后 hrtick 未重新设置的问题。当 `pick_next_task_fair()` 选择同一任务时（例如经过 `put_prev_task` + `pick_next_task` 循环），已有的 hrtick 定时器可能未被重新设置，导致该任务的调度时间片不受 hrtick 约束。Zhan Xu
- [sched-20260802-005](../../2026/08/sched-20260802-005-nohz-replace-dead-select-with-choice-default.md) `fix/low/under_review` — Kconfig 中 `select` 对 `choice` 内的选项无效，`NO_HZ_FULL` 里的 `select VIRT_CPU_ACCOUNTING_GEN` 是一行死代码。补丁删除它并改用 choice 的条件 default 表达同一关系。由静态分析工具 kconfirm 发现，已获一个非维护者的 Reviewed-by，但缺少配置验证数据且无维护者关注，存在沉寂风险。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
