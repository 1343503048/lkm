# tag: rseq

共 2 篇

- [sched-20260804-018](../../2026/08/sched-20260804-018-rseq-fix-hard-lockup-granted-time-slice-extension-v3.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical）在 08-04 按 Peter Zijlstra 的 reflow 建议定稿 v3：将 TSE 授予与 hrtimer 重排组织到已知关中断路径，避免新增 `guard(irq)()` 包装。仍 critical，待合入。
- [sched-20260803-012](../../2026/08/sched-20260803-012-rseq-fix-hard-lockup-on-granted-time-slice-extension-v2.md) `bug/critical/under_review` — rseq 时间片扩展授予路径的硬死锁（critical，08-02 系列 002）在 08-03 有新进展：Peter Zijlstra 建议用 reflow 替代新增 `guard(irq)()` 包装，更贴合既有锁上下文。仍 critical，待作者定稿 v2。
