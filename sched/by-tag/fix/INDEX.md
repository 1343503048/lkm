# tag: fix

共 2 篇

- [sched-20260817-004](../../2026/08/sched-20260817-004-sched-urgent-for-v7-2.md) `fix/medium/merged_tip` — Peter Zijlstra 的 `sched/urgent` 修复（Edgar E. Iglesias 报告）：组调度实体在 `sched_slice()` 中用**两任务 vruntime 差**而非 `cfs_rq->min_vruntime` 作基准，修复被延迟实体（DELAY_DEQUEUE）时间更新不正确的问题（`Fixes: f0f12c9b0e3e`）。Borislav 已发 PR
- [sched-20260815-014](../../2026/08/sched-20260815-014-sched-fair-fix-flat-hierarchy.md) `fix/low/merged_tip` — Vincent Guittot 的 EEVDF cgroup 权重修复由 tip-bot 合入 `sched/core`：把子权重"扁平化"，使 CPU 时间按权重比例分配，而非被层级结构过度约束。属于 08-14 系列 001（EEVDF/cgroup 权重扁平化）的延续/定稿。
