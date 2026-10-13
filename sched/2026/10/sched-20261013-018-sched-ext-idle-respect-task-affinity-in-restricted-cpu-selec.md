# sched_ext: idle: Respect task affinity in restricted CPU selection

> **subject**：sched_ext: idle: Respect task affinity in restricted CPU selection

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261011-003：Hui Su 修 sched_ext restricted `select_cpu` kfunc 路径在单 CPU / migration-disabled 任务上可能返回「不在 `p->cpus_ptr` 内」的空闲 CPU 的问题（v1 只校验 caller 的 `@allowed`）。
- sched-20261012-004：作者发 v3——因子化成 `select_cpu_restricted()`、补 `SCX_PICK_IDLE_IN_NODE` 跨 NUMA 校验；Andrea Righi 已给 `Reviewed-by`。
- sched-20261013-018（今天）：Tejun Heo 把 v3 **Applied 到 sched_ext/for-7.3-fixes** 并追加 `Reviewed-by: Andrea Righi` 标签。

## 背景与问题
（承接 20261011-003 / 20261012-004）restricted `select_cpu` kfunc 路径（`select_cpu_from_kfunc()`）对单 CPU 与 migration-disabled 任务不走 `scx_select_cpu_dfl()`，而是直接以 `prev_cpu` 为候选；`prev_cpu` 只是提示、亲和性变更后可能已不可用，加上 caller 的 `@allowed` 掩码，可能返回「不在 `p->cpus_ptr` 内」的空闲 CPU。`Fixes: 683d2d0faba1`。

## 技术方案
（承接 20261012-004）v3 把受限路径因子化为 `select_cpu_restricted()`：单 CPU 任务用 `cpumask_first(p->cpus_ptr)`、migration-disabled 任务用 `task_cpu(p)`；依次校验 `p->cpus_ptr`、caller `@allowed`，`SCX_PICK_IDLE_IN_NODE` 时再校验候选与 `prev_cpu` 同 NUMA 节点（跨节点返回 `-EBUSY`），通过后才 `scx_idle_test_and_clear_cpu()`。今日无代码变化，仅完成合入。

## 版本演进与当前进展
v3（`<20261011173100.2090211-1-sh_def@163.com>`）。今日 Tejun 应用 v3 到 `sched_ext/for-7.3-fixes` 并追加 Andrea 的 Reviewed-by。

## Maintainer 意见与讨论焦点
- **Tejun Heo**（sched_ext 维护者）：Applied 到 `sched_ext/for-7.3-fixes`。
- **Andrea Righi**（sched_ext 维护者）：Reviewed-by。
- 无异议；流程已走完。

## 合入评估
*likelihood=merged*。已合入 `sched_ext/for-7.3-fixes`。*blocking_issues*：无。*next_action*：随 for-7.3-fixes pull request 进入 7.3 主线。

## 效果评估
无性能数字；属 BPF kfunc 正确性修复（避免返回超亲和边界的空闲 CPU）。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入修复分支）；可关注 7.3 主线合入与 stable 情况。

## 参考链接
- v3 lore：https://lore.kernel.org/all/20261011173100.2090211-1-sh_def@163.com/
- 合入回帖：https://lore.kernel.org/all/d1b3d305ae23badca6eea5d7497db31c@kernel.org/

---
id: sched-20261013-018
subject: 'sched_ext: idle: Respect task affinity in restricted CPU selection'
date: 2026-10-13
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: '<20261011173100.2090211-1-sh_def@163.com>'
lore_url: 'https://lore.kernel.org/all/20261011173100.2090211-1-sh_def@163.com/'
authors:
  - 'Hui Su'
maintainers_involved:
  - 'Tejun Heo'
  - 'Andrea Righi'
current_version: v3
patch_series:
  - version: v2
    msgid: '<20261011025256.4180374-1-sh_def@163.com>'
    date: 2026-10-11
    summary: '从任务状态推导候选 CPU，claim 前做亲和校验'
    review_outcome: 'Andrea 指出漏了 SCX_PICK_IDLE_IN_NODE 校验'
  - version: v3
    msgid: '<20261011173100.2090211-1-sh_def@163.com>'
    date: 2026-10-11
    summary: 'select_cpu_restricted() 因子化 + 跨 NUMA 校验'
    review_outcome: 'Andrea Reviewed-by，Tejun 应用到 for-7.3-fixes'
upstream_commit: null
fixes_commit: '683d2d0faba1'
merged_branch: 'sched_ext/for-7.3-fixes'
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: '随 for-7.3-fixes pull request 进入 7.3 主线'
contribution_opportunities: []
generated_at: '2026-10-14T01:00:00+08:00'
source_email_count: 1
related_articles:
  - sched-20261011-003
  - sched-20261012-004
tags: [sched_ext]
---