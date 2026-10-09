# sched: Fix proxy-exec use of curr and donor

## TL;DR

本文为增量更新，完整脉络见 related_articles。

- sched-20261008-002：Jemmy Wong 发 3 枚修复，收掉 proxy execution 下三处记账不一致（NUMA/cache tick 钩子、`task_sched_runtime()` flush、`sched_can_stop_tick()` CFS 带宽检查）。Kayra Cizmeci 提醒与 Hui Su 早前补丁疑似重复。
- sched-20261009-015（今天）：**三枚全部被作者撤回**。经 Hui Su 逐一指认，三处修复分别已被 Hui Su 自己的 v5 系列（patch 1）、Hui Su 的 9 月 2 日独立补丁（patch 2）、以及 Andrea Righi 的 7 月 16 日补丁（patch 3）覆盖。Jemmy Wong 逐枚确认「I'll drop it / I'll drop this one too」，系列终结。

## 背景与问题

（承接 sched-20261008-002）proxy execution 拆分调度上下文（`rq->donor`）与执行上下文（`rq->curr`）后，`update_se()` 已把 open run interval 记到 `rq->curr`，但 tick 路径与运行时采样仍把 donor 当成「CPU 上的任务」，造成 NUMA/cache tick 钩子、运行时 flush、CFS 带宽检查三处记账不一致。今天的增量确认：这三个问题社区里已有更早、更完整的补丁在处理，本系列是重复劳动。

## 技术方案

（承接）原有三枚补丁的方案（改传 `rq->curr`、`task_sched_runtime()` 按 curr 结算、带宽检查指向 donor）本身方向正确，但今天被确认与既有工作重复：

- **patch 1 对应 Hui Su 的 v5 系列 2/4、3/4**（把 NUMA/cache tick 移到 `rq->curr`；Hui 的 1/4 是「task_tick 跑 donor 类、跨类时也跑执行类」的正确形状）。Jemmy 的版本只改 `task_tick_fair()`、漏掉「fair 锁持有者其 donor 是 RT/deadline」的情况，不如 Hui 的版本完整。
- **patch 2 对应 Hui Su 的 9 月 2 日独立补丁**（`task_sched_runtime()` 用 `task_current()` 判执行上下文、仍经 `rq->donor->sched_class` 调 `update_curr()`），改动完全相同。
- **patch 3 对应 Andrea Righi 的 7 月 16 日补丁**（NOHZ CFS 带宽检查跟随 proxy donor），且 Andrea 版额外**移除了 `nr_running == 1` 限制**——retained proxy donor 会把 donor 与 mutex owner 都留在队列里，保留该限制会在 active proxy 时跳过带宽检查；Jemmy 版保留了该 guard，不如 Andrea 版正确。

## 版本演进与当前进展

v1 发出次日即整体撤回。作者无新版本，系列终结（status=superseded）。

## Maintainer 意见与讨论焦点

- **Hui Su**（资深 sched 开发者）：逐枚指认——patch 1 与其 v5 系列 2/4、3/4 重叠；patch 2 与其 9 月 2 日独立补丁（`<20260902112539.879979-1-sh_def@163.com>`）改动相同；patch 3 与 Andrea Righi 7 月 16 日补丁（`<20260716132229.61603-2-arighi@nvidia.com>`）重叠、且 Andrea 版正确处理了 `nr_running == 1` 的保留 donor 场景。
- **Jemmy Wong（作者）**：虚心接受、逐枚确认撤回，并感谢指认。
- **Kayra Cizmeci**：昨日率先提示重叠，今日被 Hui 具体化到三个 commit/msgid。
- 结论：三个问题均已有更早/更完整的上游候选在推进，本系列为重复劳动，作者主动撤下。

## 合入评估

*likelihood=rejected*。作者已撤回全部三枚补丁，问题将由 Hui Su 系列与 Andrea Righi 的既有补丁承接。*next_action*：无，系列终结；相关修复的合入跟踪应转向 Hui Su 与 Andrea 的补丁。

## 效果评估

（承接）纯记账正确性修复、无性能数据。撤回事由是「与他人在先补丁完全重叠」，不涉及方案本身的性能争论。

## 我可以参与的点

- `discussion`：把注意力转移到三个「正主」补丁上——Hui Su 的 v5 系列与 9/2 独立补丁、Andrea Righi 的 7/16 NOHZ 补丁，这些才是 proxy-exec 记账修复的落地载体，可跟进其合入状态。
- `review`：核对 Hui Su 9/2 补丁与 Andrea 7/16 补丁的 review 进展，确认是否有新的阻塞。

## 参考链接

- Hui Su 指认: https://lore.kernel.org/all/179151887161.2196447.9527206946798924448@163.com/
- 作者撤回: https://lore.kernel.org/all/B242DE20-F1E9-4C61-894B-DC73F3884627@gmail.com/
- 系列封面: https://lore.kernel.org/all/20261008132604.98242-1-jemmywong512@gmail.com/

---
id: sched-20261009-015
date: '2026-10-09'
subject: 'sched: Fix proxy-exec use of curr and donor'
subsystem: sched
type: fix
status: superseded
severity: medium
thread_root_msgid: '<20261008132604.98242-1-jemmywong512@gmail.com>'
lore_url: 'https://lore.kernel.org/all/B242DE20-F1E9-4C61-894B-DC73F3884627@gmail.com/'
authors:
  - 'Jemmy Wong'
maintainers_involved:
  - 'Hui Su'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261008132604.98242-1-jemmywong512@gmail.com>'
    date: '2026-10-08'
    summary: 'NUMA/cache tick、runtime flush、CFS 带宽检查三处记账修复'
    review_outcome: '被 Hui Su 指认与既有补丁全面重叠，作者撤回全部三枚'
upstream_commit: null
fixes_commit: 'aa4f74dfd42b'
merged_branch: null
merge_assessment:
  likelihood: rejected
  blocking_issues:
    - '三枚均与他人在先补丁重叠，作者撤回'
  next_action: '无；跟进 Hui Su 与 Andrea 补丁的合入'
contribution_opportunities:
  - kind: discussion
    description: '跟进 Hui Su v5 与 9/2 补丁、Andrea 7/16 补丁的合入状态'
  - kind: review
    description: '核对 Hui/Andrea 两补丁的 review 进展与新阻塞'
generated_at: '2026-10-10T01:30:00'
source_email_count: 3
related_articles:
  - sched-20261008-002
tags:
  - proxy_execution
  - cfs
---