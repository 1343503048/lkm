# tag: hang

共 4 篇

- [sched-20260805-013](../../2026/08/sched-20260805-013-hung_task-v8-warning-budget-and-reporting.md) `feature/under_review` — hung_task v8 改进警告预算处理（修复「单次 hang 永久失明」），AI review 抓出数据竞争 + 日志 flood，作者已给 READ_ONCE/WRITE_ONCE + 聚合摘要修订。

- [sched-20260804-018](../../2026/08/sched-20260804-018-rseq-fix-hard-lockup-granted-time-slice-extension-v3.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。
- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
