# tag: wait

共 1 篇

- [sched-20261011-002](../../2026/10/sched-20261011-002-sched-wait-avoid-modifying-entry-on-failed-priority-registra.md) `fix/low/under_review` — Hui Su 修复 `add_wait_queue_priority_exclusive()` 的一个小正确性问题：该函数在检查是否已存在其他 priority waiter 之前就设置了 `WQ_FLAG_EXCLUSIVE` 与 `WQ_FLAG_PRIORITY`，导致注册因 `-EBUSY` 失败时，entry 未被入队却已被修改了 flags。补丁把 flags 更新移到失败检查之后。刚
