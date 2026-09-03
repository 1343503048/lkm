# tag: sched/core

共 8 篇

- [sched-20260902-016-kcov-suppress-scheduler-coverage-leaks](../../2026/09/sched-20260902-016-kcov-suppress-scheduler-coverage-leaks.md) `fix/low/under_review` — kcov（内核覆盖率工具）在调度器与定时器相关路径上会产生「覆盖泄漏」——即不应被采集的
- [sched-20260902-015-sched-remove-sched-class-balance](../../2026/09/sched-20260902-015-sched-remove-sched-class-balance.md) `fix/low/under_review` — 调度类（sched_class）的 `balance()` 回调历史上用于某个调度类的负载均衡钩子，但现代
- [sched-20260902-014-steal-governor-v11-preferred-cpu](../../2026/09/sched-20260902-014-steal-governor-v11-preferred-cpu.md) `feature/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-25 的文章）
- [sched-20260902-013-sched-clock-absolute-time-option](../../2026/09/sched-20260902-013-sched-clock-absolute-time-option.md) `feature/low/under_review` — `sched_clock` 在某些平台上基于硬件计数（如 arch timer）。当硬件时钟发生复位（reset）
- [sched-20260902-012-sched-core-wq-worker-tick-exec-ctx](../../2026/09/sched-20260902-012-sched-core-wq-worker-tick-exec-ctx.md) `fix/low/under_review` — 工作队列（workqueue）worker 的节流/记账依赖 `wq_worker_tick()` 在合适时机被调用。
- [sched-20260902-011-tip-sched-urgent-two-fixes](../../2026/09/sched-20260902-011-tip-sched-urgent-two-fixes.md) `fix/medium/merged_tip` — 09-02 `tip/sched/urgent` 合入两笔修复，分别来自调度核心与 x86 调度相关代码：
- [sched-20260902-002-preempt-dynamic-static-key-migration](../../2026/09/sched-20260902-002-preempt-dynamic-static-key-migration.md) `fix/low/merged_tip` — 09-02 一批 `sched/core` 与 `sched: dynamic` 的清理改动合入 `tip/sched/core`，分成两条
- [sched-20260902-001-proxy-execution-batch-merge](../../2026/09/sched-20260902-001-proxy-execution-batch-merge.md) `feature/medium/merged_tip` — Proxy Execution（PE，解决优先级翻转 / 锁持有者代理运行）在 09-02 有一批改动合入