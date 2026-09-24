# tag: rt_bandwidth

共 1 篇

- [sched-20260924-001](../../2026/09/sched-20260924-001-sched-rt-rebuild-domains-only-after-successful-rt-sysctl-wri.md) `fix/medium/under_review` — Joseph Salisbury 的修复补丁：把 `rebuild_sched_domains()` 从「每次 RT sysctl 写入前无条件执行」改为「仅当写入成功且值真实变化时」才执行，消除 RT 周期/运行时间参数每次读取都触发全量调度域重建的开销。本日 Chengfeng Lin 给出独立实测：在 v7.2 上该补丁把 RT sysctl 读延迟从约 8.57us 降到 0.264us（
