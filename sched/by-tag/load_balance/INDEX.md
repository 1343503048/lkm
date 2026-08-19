# tag: load_balance

共 1 篇

- [sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion](../../2026/08/sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion.md) `feature/low/under_review` — `[PATCH 0/2] sched: Remove sched_class::balance()` 系列在 8/19 有多封回复，讨论焦点是与 core_sched 的交互正确性（在 pick 内做 balance 可能错移任务、core-sched 下 RETRY_TASK 语义存疑）。本次抓取未拿到原始 cover，方案全貌与作者待补；合入前景 medium，受同日 core_sched 竞态分析（article 002）牵连。