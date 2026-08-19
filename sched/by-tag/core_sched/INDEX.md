# tag: core_sched

共 2 篇

- [sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion](../../2026/08/sched-20260819-011-sched-remove-sched-class-balance-core-sched-discussion.md) `feature/low/under_review` — `[PATCH 0/2] sched: Remove sched_class::balance()` 系列在 8/19 有多封回复，讨论焦点是与 core_sched 的交互正确性（在 pick 内做 balance 可能错移任务、core-sched 下 RETRY_TASK 语义存疑）。本次抓取未拿到原始 cover，方案全貌与作者待补；合入前景 medium，受同日 core_sched 竞态分析（article 002）牵连。
- [sched-20260819-002-core-sched-pick-task-race-null-deref-discussion](../../2026/08/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.md) `discussion/high/under_review` — core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续，造成 `rqX->core_pick` 被对端置 NULL 后空指针解引用。Peter 8/19 回复承认这是个漂亮竞态，但尚无好修复，且 sched_ext 参与让问题更复杂。属于 08-17→08-18 core_sched/proxy_exec 讨论线的延续。