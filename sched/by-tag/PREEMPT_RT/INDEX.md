# tag: PREEMPT_RT

共 1 篇

- [sched-20260821-002](../../2026/08/sched-20260821-002-sched-allow-sleeping-spinlocks-on-preempt-rt-within-non-block.md) `fix/low/under_review` — PREEMPT_RT 下 non_block_start()/end() 区间内获取 sleeping spinlock 会触发 might_sleep() 告警。Sebastian 的修复为 `__might_resched()` 增加 `sleeping_lock` 参数区分正常调度与 sleeping lock 调度，David Woodhouse 已 ack。
