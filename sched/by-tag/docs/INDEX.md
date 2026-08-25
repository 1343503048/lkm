# tag: docs

共 3 篇

- [sched-20260824-003](../../2026/08/sched-20260824-003-docs-sched_ext-cgroup-knobs.md) `discussion/under_review` — 本文为增量更新，完整背景见 related_articles 中的文章。Tao Cui 的文档补丁从 v3 推进到 v4，根据 Andrea Righi 的建议修改了措辞，明确了 `ops.cgroup_init()` 和 `ops.cgroup_set_*()` 的传递机制。
- [sched-20260814-005](../../2026/08/sched-20260814-005-documentation-sched-ext-fix-events-sysfs-path-and-show-state.md) `docs/low/under_review` — Tao Cui 提交 v2（2 patches）「sched_ext: minor doc and comment fixes」。纯文档/注释修正（events sysfs 路径、show_state 示例、stale 引用、%SCX_DEQ 命名），无功能改动。合入可能性 high。
- [sched-20260804-017](../../2026/08/sched-20260804-017-sched-docs-document-cpu_preferred_mask.md) `feature/under_review` — Shrikanth Hegde 把 `cpu_preferred_mask`（per-task 偏好的大/小核子集，用于节能与缓存热）概念文档化，作为 cpu_preferred_mask 系列（v9→v10）的一部分。作者公开表示仍在等待一组 benchmark 数字支撑合入。合入可能性 medium——明确等数据。
