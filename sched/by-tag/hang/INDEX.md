# tag: hang

共 6 篇

- [sched-20260901-014](../../2026/09/sched-20260901-014-deadlock-from-exec-update-lock-and-reading-procfs.md) `bug/critical/under_review` — Benjamin Peterson 报告：带上 `6650527444da ("proc: protect ptrace_may_access() with exec_update_lock (part 1)")` 之后，FUSE 服务器在实际负载下死锁——正在 `execve` 的进程在 `do_close_on_exec()` 里关 O_CLOEXEC 文件、同步等 FUSE 回复，而 FUS
- [sched-20260827-005](../../2026/08/sched-20260827-005-question-userspace-throttling-sched-fair-combine-detach-into.md) `bug/high/under_review` — 本文为增量更新（完整背景见 related_articles）。chenjinghuang（Huawei）与 Aaron Lu（ByteDance）在 08-27 把 guest 启动挂起问题的边界钉得更实：复现需要 **CPU 超额订阅 + 大量 vCPU**，96 vCPU 不复现、128 vCPU 复现；必须同时 revert `e1f078f50478`（Combine detach in
- [sched-20260805-013](../../2026/08/sched-20260805-013-hung_task-v8-warning-budget-and-reporting.md) `feature/under_review`
- [sched-20260804-018](../../2026/08/sched-20260804-018-rseq-fix-hard-lockup-granted-time-slice-extension-v3.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。
- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
- [sched-20260802-002](../../2026/08/sched-20260802-002-rseq-fix-hard-lockup-on-granted-time-slice-extension.md) `bug/critical/under_review` — `rseq` 的时间片扩展（Time Slice Extension，TSE）在**开中断**状态下调用了要求**关中断**的 `hrtimer_rearm_deferred_tif()`，造成 `hrtimer_bases.lock` 的中断上下文锁反转，重负载使用 TSE 时会硬死锁。修复只有一行 `guard(irq)()`。有 lockdep 实证、有真实死锁现象，严重度 critical
