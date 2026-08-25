---
layout: default
tag: "race_condition"
title: "标签: race_condition"
article_count: 5
---

- [sched-20260824-005](/lkm/2026/08/24/sched-20260824-005-sched-lift-cgroup-locking-core.html) `fix/medium/under_review` — sched: 提升 cgroup 更新锁到核心层（增量更新）
- [sched-20260824-006](/lkm/2026/08/24/sched-20260824-006-sched-fair-null-deref-v4.19.html) `bug/critical/under_review` — sched/fair: pick_next_task_fair NULL 解引用（v4.19 生产环境）
- [sched-20260824-007](/lkm/2026/08/24/sched-20260824-007-sched-core-stale-rq-curr-arm64.html) `bug/critical/under_review` — sched/core: ARM64 服务器偶发 rq->curr 过期导致调度器崩溃
- [sched-20260821-001](/lkm/2026/08/21/sched-20260821-001-sched-lift-cgroup-update-locking-to-core-to-prevent-cfs-scx-divergence.html) `fix/medium/under_review` — 并发写入 cgroup 控制文件（如 cpu.shares/cpu.weight）会导致 CFS 与 SCX 之间的状态不一致
- [sched-20260821-006](/lkm/2026/08/21/sched-20260821-006-sched-ext-serialize-concurrent-cpu-max-writers-in-scx-group-set-bandwidth.html) `fix/medium/under_review` — 并发写入同一 cgroup 的 cpu.max 会导致 SCX 侧的 `ops.cgroup_set_bandwidth()` 回调和 `tg->scx....
