# tag: dvfs

共 1 篇

- [sched-20261004-004](../../2026/10/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.md) `bug/medium/under_review` — Tao Cui（KylinOS）的单补丁修复 sched_ext 子调度器 DVFS 残留问题：持有 `SCX_CAP_PERF` 的子调度器设了一个低 cpuperf target 后退场——cap 被回收（revoke）、被 kill、detach 或 cgroup 摘除——`rq->scx.cpuperf_target` 却留在原地。`scx_bpf_sub_revoke()` 只清 psh
