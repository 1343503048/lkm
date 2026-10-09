# tag: proxy_exec

共 2 篇

- [sched-20261003-001](../../2026/10/sched-20261003-001-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
- [sched-20261002-008](../../2026/10/sched-20261002-008-sched-ext-keep-proxy-donors-with-slice-left-on-the-local-dsq.md) `fix/low/under_review` — Andrea Righi（NVIDIA，sched_ext 维护者）直接发往 `sched_ext/for-7.4` 分支的单补丁修复：commit ee172227d0dc（"Delegate proxy donor admission to BPF schedulers"）让 `put_prev_task_scx()` 把保留的 proxy donor 以 `SCX_ENQ_BLOCKED` 
