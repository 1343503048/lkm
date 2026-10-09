# tag: procfs

共 1 篇

- [sched-20261003-003](../../2026/10/sched-20261003-003-sched-numa-ngid-is-reported-as-a-global-pid-inside-a-pid-namesp.md) `bug/medium/under_review` — Maoyi Xie 报告一个 pid namespace 隔离缺口：`/proc/<pid>/status` 的 `Ngid` 字段（NUMA group id）没有像同函数打印的其他 pid 一样做 namespace 转换——`task_state()` 里 ppid/tgid 都走 `task_*_nr_ns(p, ns)`，唯独 `ngid = task_numa_group_id(p)`
