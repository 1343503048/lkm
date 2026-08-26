# tag: bandwidth

共 1 篇

- [sched-20260818-004](../../2026/08/sched-20260818-004-sched-ext-allow-ops-cgroup-set-bandwidth-to-be-sleepable.md) `feature/medium/under_review` — Changwoo Min 提交单 patch 将 `ops.cgroup_set_bandwidth()` 加入 sched_ext cgroup 操作的 sleepable 白名单，使 BPF 调度器在 cgroup 获得 cpu.max 限制时可按需分配内存，而非预保留。Tejun Heo review 要求加 `__retain`、统一 marker 前缀并集中放置。
