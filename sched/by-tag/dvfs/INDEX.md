# tag: dvfs

共 3 篇

- [sched-20261007-003](../../2026/10/sched-20261007-003-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.md) `fix/medium/superseded` — - sched-20261004-004：Tao Cui 报告并修复 sched_ext 子调度器生命周期漏洞——持有 `SCX_CAP_PERF` 的子调度器把 cpuperf target 写低后消失（cap 回收/kill/detach/cgroup 移除），target 残留：`scx_bpf_sub_revoke()` 只清 caps 位图、`scx_sub_disable()` 重定任
- [sched-20261006-006](../../2026/10/sched-20261006-006-sched-ext-reset-cpuperf-target-when-a-sub-loses-scx-cap-perf.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261004-004](../../2026/10/sched-20261004-004-sched-ext-reset-cpuperf-target-when-a-sub-scheduler-loses-sc.md) `bug/medium/under_review` — Tao Cui（KylinOS）的单补丁修复 sched_ext 子调度器 DVFS 残留问题：持有 `SCX_CAP_PERF` 的子调度器设了一个低 cpuperf target 后退场——cap 被回收（revoke）、被 kill、detach 或 cgroup 摘除——`rq->scx.cpuperf_target` 却留在原地。`scx_bpf_sub_revoke()` 只清 psh
