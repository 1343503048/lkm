---
layout: default
tag: "memory_safety"
title: "标签: memory_safety"
article_count: 2
---

- [sched-20260824-007](/lkm/2026/08/24/sched-20260824-007-sched-core-stale-rq-curr-arm64.html) `bug/critical/under_review` — sched/core: ARM64 服务器偶发 rq->curr 过期导致调度器崩溃
- [sched-20260821-011](/lkm/2026/08/21/sched-20260821-011-cpuidle-dt-idle-genpd-kfree-the-original-name-allocation.html) `fix/medium/under_review` — `dt_idle_pd_alloc()` 中 `pd->name` 指向 `kasprintf()` 分配内存的中间位置（`kbasename()` 偏移）
