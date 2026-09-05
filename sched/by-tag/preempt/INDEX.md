# tag: preempt

共 4 篇

- [sched-20260905-004](../../2026/09/sched-20260905-004.md) `patch_series/low/merged` — 提交 `ef9293b3b797` "sched: dynamic: Fix preemption model strings" 进入 `tip/sched/core`，并通过 0day 74 个 config 构建（BUILD SUCCESS）。该修复修正 PREEMPT_DYNAMIC 下抢占模型字符串的显示/取值问题，属 PREEMPT_DYNAMIC 简化工作的后续收尾。
- [sched-20260903-013](../../2026/09/sched-20260903-013.md) `patch_series/medium/under_review` — 在 09-02 已合入的 PREEMPT_DYNAMIC 简化基础上，本系列（v2，0/6）进一步清理与精简 PREEMPT_DYNAMIC 的实现与静态分支选择逻辑，降低维护成本并移除遗留分支。
- [sched-20260902-014-steal-governor-v11-preferred-cpu](../../2026/09/sched-20260902-014-steal-governor-v11-preferred-cpu.md) `feature/medium/under_review` — （本文为增量更新，完整背景见 related_articles 中 08-25 的文章）
- [sched-20260902-002-preempt-dynamic-static-key-migration](../../2026/09/sched-20260902-002-preempt-dynamic-static-key-migration.md) `fix/low/merged_tip` — 09-02 一批 `sched/core` 与 `sched: dynamic` 的清理改动合入 `tip/sched/core`，分成两条