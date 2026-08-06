# tag: core_sched

共 4 篇

- [sched-20260806-010](../../2026/08/sched-20260806-010-sched-ext-proxy-execution-conservative-terminate.md) `feature/under_review` — proxy execution 跨类代理难题：转向类边界 terminate。延续 08-05-001。
- [sched-20260806-011](../../2026/08/sched-20260806-011-sched-wake_q-stable-6.12y-helper.md) `fix/low/under_review` — wake_q 辅助函数 6.12.y 稳定回引（wake_q 属 core 调度基础设施）。

- [sched-20260805-001](../../2026/08/sched-20260805-001-sched-ext-proxy-exec-reject-dsq-class-transition.md) `feature/under_review` — Andrea Righi 的 sched_ext proxy execution 系列中，07/15 讨论「跨调度类切换时阻断 proxy donor」：因 RT/DL PI 需要跨类保留 donor，不能全局无条件阻断，应作为 per-class「支持保留 proxy donor」能力泛化。涉及 core scheduling 的代理执行语义。
- [sched-20260730-001](../../2026/07/sched-20260730-001-sched-fix-sched-flag-keep-params-side-effects.md) `fix/medium/under_review` — Andrea Righi 修复了 `SCHED_FLAG_KEEP_PARAMS` 标志的两个副作用：即使设置了该标志，`__sched_setscheduler()` 仍会错误地触发 class 切换回调和 deadline 带宽记账。v1 刚发出，PeterZ 已 review，合入可能性高。
