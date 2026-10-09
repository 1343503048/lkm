# tag: fair

共 2 篇

- [sched-20261002-012](../../2026/10/sched-20261002-012-sched-fair-remove-tunable-scaling.md) `discussion/rfc` — Tor Vic（社区贡献者，自述「not a developer」）的 2 补丁 RFC：删除 2.6.33 时代引入的调度器可调参数缩放机制。1/2 先删基本无人用的 `none`/`linear` 缩放（保留默认的 logarithmic），debugfs 直设 `sched_base_slice` 仍可用；2/2 更进一步删掉整个缩放机制、把 `sched_base_slice` 固定为 2
- [sched-20261002-011](../../2026/10/sched-20261002-011-sched-fair-rework-fix-task-h-load.md) `fix/medium/under_review` — 本文为增量更新，完整脉络见 related_articles。
