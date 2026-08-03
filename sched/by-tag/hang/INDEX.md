# tag: hang

共 2 篇

- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
