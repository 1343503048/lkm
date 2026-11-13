# tag: wait

共 5 篇

- [sched-20261113-005](../../2026/11/sched-20261113-005-sched-wait-kill-leftover-bookmark-logic-in-wake-up-common.md) `fix/under_review` — Oleg Nesterov 提交单补丁清理 `__wake_up_common()` 里的死代码：`list_first_entry` 手动头检查 + `list_for_each_entry_safe_from()` 是 commit `2554db916586`（"sched/wait: Break up long wake list walk"）遗留的 bookmark 逻辑，其主体已被 `
- [sched-20261112-005](../../2026/11/sched-20261112-005-sched-wait-queue-non-exclusive-waiters-at-the-head-in-do-wai.md) `bug/high/under_review` — Mani Tofigh 修一个可让任务永久睡眠的 waitqueue 缺陷：`wait_event_interruptible_locked_irq()`（eventfd/timerfd 用）把非独占读等待者加到队列尾部，若同一文件上先加了一个 `EPOLLEXCLUSIVE` 的 epoll 观察者，`__wake_up_common()` 唤醒独占条目后就停，被唤醒的 epoll 任务若被杀或
- [sched-20261015-027](../../2026/10/sched-20261015-027-sched-wait-avoid-modifying-entry-on-failed-priority-registra.md) `fix/low/merged_tip` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261012-016](../../2026/10/sched-20261012-016-sched-wait-avoid-modifying-entry-on-failed-priority-registra.md) `fix/low/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261011-002](../../2026/10/sched-20261011-002-sched-wait-avoid-modifying-entry-on-failed-priority-registra.md) `fix/low/under_review` — Hui Su 修复 `add_wait_queue_priority_exclusive()` 的一个小正确性问题：该函数在检查是否已存在其他 priority waiter 之前就设置了 `WQ_FLAG_EXCLUSIVE` 与 `WQ_FLAG_PRIORITY`，导致注册因 `-EBUSY` 失败时，entry 未被入队却已被修改了 flags。补丁把 flags 更新移到失败检查之后。刚
