# tag: numa

共 2 篇

- [sched-20260803-006](../../2026/08/sched-20260803-006-sched-numa-prevent-race-on-sysctl_numa_balancing-static-key.md) `bug/high/under_review` — `sched/numa` 修复 `sysctl_numa_balancing` 静态键切换时的抢占竞态（UAF / use-after-uninit），附 syzkaller C repro 与 Fixes 标签。问题真实且有复现，合入可能性高。
- [sched-20260803-009](../../2026/08/sched-20260803-009-sched-numa-apply-remote-socket-distance-averaging-for-hygon-7447v.md) `feature/under_review` — `sched/numa` 针对 Hygon 7447V 的模块化布局，把远程 socket 节点距离取平均以区分 intra/inter-socket 远程代价。已获 Ingo Acked-by，合入可能性高。
