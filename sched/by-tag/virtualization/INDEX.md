# tag: virtualization

共 2 篇

- [sched-20260824-008](../../2026/08/sched-20260824-008-sched-core-defer-vcpu-task-clock.md) `feature/low/rfc` — KVM 客户机中，当 vCPU A 为被抢占的 vCPU B 做记账时，由于 KVM host 直到 vCPU B 重新进入才更新 stealtime，导致 vCPU A 无法观察到 steal 时间，错误地将 stolen 区间计入任务运行时间。RFC 提出延迟远程 CPU 对已标记为 preempted 的 vCPU 的 `clock_task` 更新。
- [sched-20260822-003](../../2026/08/sched-20260822-003-steal-governor-v10-benchmark-3-5pct-regression.md) `discussion/under_review` — steal_governor v10 系列收到 Yury 的独立测试：steal ratio 成功收敛，但整体性能比基线差 3-5%。作者需要调查性能回退原因。
