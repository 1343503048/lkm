# tag: proxy_execution

共 1 篇

- [sched-20260819-002-core-sched-pick-task-race-null-deref-discussion](../../2026/08/sched-20260819-002-core-sched-pick-task-race-null-deref-discussion.md) `discussion/high/under_review` — core_sched 在 `pick_task()` 释放 core-wide 锁后未触发 `RETRY_TASK` 而继续，造成 `rqX->core_pick` 被对端置 NULL 后空指针解引用。Peter 8/19 回复承认这是个漂亮竞态，但尚无好修复，且 sched_ext 参与让问题更复杂。属于 08-17→08-18 core_sched/proxy_exec 讨论线的延续。