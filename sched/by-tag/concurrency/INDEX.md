# tag: concurrency

共 1 篇

- [sched-20261003-004](../../2026/10/sched-20261003-004-sched-ext-generate-qseq-from-a-per-task-counter.md) `fix/medium/under_review` — Kuba Piecuch（Google）发往 `sched_ext/for-7.3-fixes` 的单补丁正确性修复：`finish_dispatch()` 用 `ops_state` 里的 qseq 判断要 claim 的 QUEUED 实例是否就是 `scx_bpf_dsq_insert()` 当时看到的那个，但 qseq 取自 **rq 级**计数器 `rq->scx.ops_qseq`——
