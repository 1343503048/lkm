# sched_ext: Don't route tasks to SCX before __scx_enabled is fully patched

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261118-012：Kuba Piecuch（Google）为 sched_ext/for-7.4-fixes 发修复——`static_branch_enable(&__scx_enabled)` 按地址序而非原子地 patch jump-label，`task_should_scx()` 可能先于 `__schedule()` 被 patch，导致并发 fork/sched_setscheduler 在窗口期内把任务迁到 ext 类，触发 `put_prev_task_scx` WARNING；修复用带 release 语义的标志把任务路由门控推迟到 patch 完成。Andrea Righi 给 Reviewed-by，Tao Cui 实测复现/修复并给 Tested-by。
- sched-20261119-007（今天）：**Tejun Heo 已收**——`Applied to sched_ext/for-7.4-fixes`，并补 `Reviewed-by: Andrea Righi`、`Tested-by: Tao Cui`、`Reviewed-by: Tao Cui` 三枚 tag。修复进入 sched_ext 的 7.4-fixes 分支。

## 背景与问题

（承接 sched-20261118-012）`scx_root_enable_workfn()` 先置 `scx_switching_all` 并调 `static_branch_enable(&__scx_enabled)` 再切换任务，而 `task_should_scx()` 只以 `scx_enabled()` 为门控。`static_branch_enable()` 按地址顺序 patch 各 jump-label 站点、并非原子：`task_should_scx()` 可能先于 `__schedule()` 被 patch。若此时并发 fork/sched_setscheduler 进入窗口，`task_should_scx()` 观察到 `scx_enabled()`，把运行任务从 fair 迁到 ext 类并在类退化时置 need_resched；随后的 `__schedule()` 仍在 `next_active_class()` 里读到 `!scx_enabled()`、跳过 ext 类并选中 `rq->idle`，而 runnable 的 SCX 任务仍是 `rq->donor`，触发 `WARNING: kernel/sched/ext/ext.c:3840 put_prev_task_scx`。`Fixes: f0e1a0643a59 ("sched_ext: Implement BPF extensible scheduler class")`，Cc stable v6.12+。

## 技术方案

（承接 20261118-012）用一个带 release 语义的标志，把「任务路由到 SCX」的门控推迟到 `__scx_enabled` 静态分支完整 patch 之后，消除窗口期内「任务已迁入 ext 类、但 `__schedule()` 仍不认 ext 类」的不一致。

## 版本演进与当前进展

*current_version: v1（2026-11-18，`<20261118102453.1315267-1-jpiecuch@google.com>`）*。今日无新版本，直接由 Tejun 收取进 `sched_ext/for-7.4-fixes`。

## Maintainer 意见与讨论焦点

- **Tejun Heo（sched_ext 维护者）**：`Applied to sched_ext/for-7.4-fixes`，附 `Reviewed-by: Andrea Righi <arighi@nvidia.com>`、`Tested-by: Tao Cui <cuitao@kylinos.cn>`、`Reviewed-by: Tao Cui <cuitao@kylinos.cn>`。
- 无 NAK、无未解决分歧；修复路径与测试证据齐备。

## 合入评估

*likelihood=merged*。已进入 `sched_ext/for-7.4-fixes`，待随 sched_ext 修复分支汇入主线。*blocking_issues*：无。*next_action*：等待并入 tip/主线，并视需回合 stable v6.12+。

## 效果评估

Tao Cui 实测（承接 20261118-012）：25 次 scx_simple 加载/卸载 + fork/sched_setscheduler 风暴下，基线复现 `put_prev_task_scx` 告警、补丁后 0 告警。

## 我可以参与的点

当前阶段暂无明显参与空间（已合入 sched_ext/for-7.4-fixes）；可持续观察是否回合 stable v6.12+ 及是否有后续回归。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261118102453.1315267-1-jpiecuch@google.com/
- Tejun 收取回复: https://lore.kernel.org/all/a41504e9f5b99dd12d4e47ee9b54411d@kernel.org/

---
id: sched-20261119-007
date: '2026-11-19'
subject: "sched_ext: Don't route tasks to SCX before __scx_enabled is fully patched"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261118102453.1315267-1-jpiecuch@google.com>"
lore_url: "https://lore.kernel.org/all/20261118102453.1315267-1-jpiecuch@google.com/"
authors: [Kuba Piecuch]
maintainers_involved: [Tejun Heo]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261118102453.1315267-1-jpiecuch@google.com>"
    date: '2026-11-18'
    summary: "带 release 语义标志推迟任务路由到 SCX 的门控"
    review_outcome: "Andrea Righi/Tao Cui Reviewed-by、Tao Cui Tested-by；Tejun 收进 for-7.4-fixes"
upstream_commit: null
fixes_commit: "f0e1a0643a59"
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "等待并入 tip/主线，视需回合 stable v6.12+"
contribution_opportunities: []
generated_at: "2026-11-20T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261118-012]
tags: [sched_ext]
---