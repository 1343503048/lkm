# sched_ext: Don't route tasks to SCX before __scx_enabled is fully patched

## TL;DR

Kuba Piecuch（Google）为 sched_ext/for-7.4-fixes 发修复：启用 SCX 时 `static_branch_enable(&__scx_enabled)` 按地址序而非原子地 patch jump-label 站点，`task_should_scx()` 可能先于 `__schedule()` 被 patch，导致并发 fork/sched_setscheduler 在窗口期内把任务迁到 ext 类，而 `__schedule()` 仍读到 `!scx_enabled` 跳过 ext 类、选中 idle 却留下 runnable 的 SCX 任务作 donor，触发 `put_prev_task_scx` WARNING。修复用一个带 release 语义的标志把任务路由门控推迟到 patch 完成后。Andrea Righi 给 Reviewed-by，Tao Cui 实测（25 次 scx_simple 加载/卸载、fork+sched_setscheduler 风暴）复现基线告警、补丁后 0 告警并给 Tested-by。

## 背景与问题

`scx_root_enable_workfn()` 先置 `scx_switching_all` 并调 `static_branch_enable(&__scx_enabled)` 再切换任务，而 `task_should_scx()` 只以 `scx_enabled()` 为门控。`static_branch_enable()` 按地址顺序 patch 各 jump-label 站点、并非原子：`task_should_scx()` 可能先于 `__schedule()` 被 patch。若此时并发 fork/sched_setscheduler 进入窗口，`task_should_scx()` 观察到 `scx_enabled()`，把运行任务从 fair 迁到 ext 类并在类退化时置 need_resched；随后的 `__schedule()` 仍在 `next_active_class()` 里读到 `!scx_enabled()`、跳过 ext 类并选中 `rq->idle`，而 runnable 的 SCX 任务仍是 `rq->donor`，触发 `WARNING: kernel/sched/ext/ext.c:3840 put_prev_task_scx`。`Fixes: f0e1a0643a59 ("sched_ext: Implement BPF extensible scheduler class")`，Cc stable v6.12+。

## 技术方案

给 `task_should_scx()` 增加一个 `scx_task_switch_enabled` 标志门控：该标志带 release 语义、仅在 `static_branch_enable(&__scx_enabled)` 完成全部调用点 patch 且 `scx_switching_all` 更新之后置位；disable 路径与 `scx_switching_all` 一起清除。改动 `kernel/sched/ext/ext.c` +17/-3。作者注明本 bug 由 AI 编码助手协助发现与编写。

## 版本演进与当前进展

*current_version: v1（2026-11-18 发出，`<20261118102453.1315267-1-jpiecuch@google.com>`）*。当日获 Andrea Righi 的 Reviewed-by、Tao Cui 的 Reviewed-by + Tested-by，无反向意见。

## Maintainer 意见与讨论焦点

- **Andrea Righi（sched_ext 维护者）**：`Reviewed-by`（「Looks good, good catch」）。
- **Tao Cui（reviewer/tester）**：release/acquire 门控在 enable/disable 路径均正确；在 700a332c3fe3（for-7.4-fixes HEAD）上跑 25 次 scx_simple 加载/卸载 + fork/sched_setscheduler 风暴，基线 14s 即触发报告告警（栈含 `put_prev_task_scx+0x4e4`），补丁后同样流程 0 告警；给 Tested-by + Reviewed-by。
- 无 NAK、无未解决分歧。

## 合入评估

*likelihood=high*。sched_ext/for-7.4-fixes 的紧急修复，已获维护者 RB 与测试背书，带 `Fixes:` + Cc stable，属典型的快速收取。*blocking_issues*：无实质阻塞。*next_action*：Tejun Heo 收取进入 sched_ext/for-7.4-fixes。

## 效果评估

Tao Cui 实测：基线在约 14s 触发 `WARNING: kernel/sched/ext/ext.c:3840 put_prev_task_scx`（栈 `__schedule → preempt_schedule_common → __sched_setscheduler`），补丁后 25 次相同加载/卸载 + 风暴流程 0 告警。属正确性修复，无性能数据。

## 我可以参与的点

- **testing**：在不同 BPF 调度器（scx_flatcg/scx_simple）与 `scx_switching_all` 场景下跑 enable/disable 风暴，验证无 `put_prev_task_scx` 告警、无任务被误留为 donor。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261118102453.1315267-1-jpiecuch@google.com/
- Andrea Righi 的 RB: https://lore.kernel.org/all/av20PBaLcuPwDf_l@gpd4/
- Tao Cui 的测试: https://lore.kernel.org/all/11f7d4ff-b3f1-4d8c-a37c-887d354596da@linux.dev/

---
id: sched-20261118-012
date: '2026-11-18'
subject: "sched_ext: Don't route tasks to SCX before __scx_enabled is fully patched"
subsystem: sched
type: fix
status: under_review
severity: high
thread_root_msgid: "<20261118102453.1315267-1-jpiecuch@google.com>"
lore_url: "https://lore.kernel.org/all/20261118102453.1315267-1-jpiecuch@google.com/"
authors: [Kuba Piecuch]
maintainers_involved: [Andrea Righi]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261118102453.1315267-1-jpiecuch@google.com>"
    date: '2026-11-18'
    summary: "新增 scx_task_switch_enabled 门控，推迟任务路由到 patch 完成后"
    review_outcome: "Andrea Righi RB，Tao Cui Tested-by/RB"
upstream_commit: null
fixes_commit: "f0e1a0643a59"
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: "Tejun Heo 收取进入 sched_ext/for-7.4-fixes"
contribution_opportunities:
  - kind: testing
    description: "多 BPF 调度器 + switching_all 场景跑 enable/disable 风暴验证无告警"
generated_at: "2026-11-19T09:00:00+08:00"
source_email_count: 3
related_articles: []
tags: [sched_ext]
---
