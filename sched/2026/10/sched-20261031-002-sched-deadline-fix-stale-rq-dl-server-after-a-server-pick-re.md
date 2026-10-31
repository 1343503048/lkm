# sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK

## TL;DR
Tejun Heo 最初发了一版 `[PATCH sched/urgent]` 修 `__pick_task_dl()` 在 server pick 返回 `RETRY_TASK` 时也把 server 记进 `rq->dl_server`、导致重启的 pick 把「陈旧 server」塞给无关任务的缺陷；随后两封回帖自撤回——「发错补丁了」，改成发**带 reproducer 的 bug 报告**，表示将测试 Juri 的补丁。Andrea Righi 在相邻 sched_ext 线程里也独立点名了同一 `dl_server` 问题，认为它与 sched_ext 的 stale pick 是两件事。截至当日该 bug 尚无被合入/认可的修复。

## 背景与问题
Tejun 的报告（`<6db076ee2562b5fb84d70ed59abe670e@kernel.org>`）：`__pick_task_dl()` 在 server pick 返回 `RETRY_TASK` 时**也会**把 server 记录到 `rq->dl_server`；而 `__pick_next_task()` 只在 `restart` 标签**之上**清除它，因此重启后的 pick 会把陈旧 server 交给它所选中的任务。该路径自 `b3a2dfa8b42e`（"sched/fair: Add newidle balance to pick_task_fair()"）变得可达——该 commit 使 `fair_server_pick_task()` 在 newidle balance 释放 rq lock 期间有更高类任务入队时返回 `RETRY_TASK`。复现：mainline `abf8c33470f7`、8-CPU VM，60s/500µs 延迟的 reproducer，6 次运行分别计到 8、44、0、7、24、22 次「stale rq->dl_server handed to RT task」；但**未观察到该陈旧指针的运行时副作用**。

## 技术方案
被撤回的原补丁（`kernel/sched/deadline.c` +7）方向是「server pick 返回 `RETRY_TASK` 时不记录 server」，让重启后的 pick 自行记录。Andrea Righi 提的备选方向是「重启时清除 `rq->dl_server`」。截至当日两案均未定案，无正式可合入补丁。

## 版本演进与当前进展
*current_version: null*（补丁已被作者撤回）。当日时序：Tejun 先发 `[PATCH sched/urgent]`（`<20261030221842.4071610-1-tj@kernel.org>`）→ 回帖「please ignore this one, sent out the wrong patch, I'll test Juri's」→ 再发 bug 报告 + reproducer（`<6db076ee2562b5fb84d70ed59abe670e@kernel.org>`）。

## Maintainer 意见与讨论焦点
- **Tejun Heo（报告者，sched_ext 维护者）**：自撤回补丁，明确此 bug 的修复交给 Juri 方向。
- **Andrea Righi（sched_ext co-maintainer，在 sched_ext 线程中）**：认可 Sashiko 的 dl_server 发现有效，但定性为「独立的 core 调度器 bug，应另行处理」，并追问「是否应在 restart 时清除 rq->dl_server（我未复现/测试过）」。
- 无 NAK；争议点仅剩修法形态（不记录 vs restart 清除）。

## 合入评估
*likelihood=unknown*。bug 真实、有 reproducer 与 `Fixes:` 指向 `b3a2dfa8b42e`，但修复补丁被作者撤回、方向尚未定案，且当前无任何实测副作用，优先级与修复形态均待定。*blocking_issues*：修复补丁被撤回，需 Juri（或 Tejun）给出可合入补丁；「不记录 vs restart 清除」未收敛。*next_action*：等 Juri 方向补丁成形并实测。

## 效果评估
无性能数据。Tejun 给出定量复现（6 次运行 hand-off 计数 8/44/0/7/24/22），并明确「未观察到陈旧指针的运行时影响」——即正确性 bug 但当前无可见危害。

## 我可以参与的点
- **testing**：跑 Tejun 的 reproducer（8-CPU VM + stress-ng + debug patch 拉宽 newidle lock drop），确认 hand-off 计数，并验证候选修复后归零。
- **review**：分析「RETRY_TASK 时不记录 server」vs「restart 时清除 dl_server」两种修法在 `__pick_next_task()` 重入路径下的等价性与边界。

## 参考链接
- Tejun 被撤回的补丁: https://lore.kernel.org/all/20261030221842.4071610-1-tj@kernel.org/
- Tejun 的 bug 报告（含 reproducer）: https://lore.kernel.org/all/6db076ee2562b5fb84d70ed59abe670e@kernel.org/

---
id: sched-20261031-002
date: 2026-10-31
subject: "sched/deadline: Fix stale rq->dl_server after a server pick returns RETRY_TASK"
subsystem: sched
type: bug
status: rfc
severity: medium
thread_root_msgid: "<20261030221842.4071610-1-tj@kernel.org>"
lore_url: "https://lore.kernel.org/all/20261030221842.4071610-1-tj@kernel.org/"
authors: [Tejun Heo]
maintainers_involved: []
current_version: null
patch_series: []
upstream_commit: null
fixes_commit: b3a2dfa8b42e
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues:
    - "修复补丁被作者撤回，需 Juri（或 Tejun）给出可合入补丁"
    - "「RETRY_TASK 时不记录 server」vs「restart 时清除 dl_server」两种修法未收敛"
  next_action: "等 Juri 方向的 dl_server 补丁成形并实测"
contribution_opportunities:
  - kind: testing
    description: "跑 Tejun 的 reproducer（8-CPU VM + stress-ng），验证候选修复后 hand-off 归零"
  - kind: review
    description: "分析两种修法在 __pick_next_task() 重入路径下的等价性与边界"
generated_at: "2026-11-01T09:00:00"
source_email_count: 3
related_articles: []
tags: [deadline, dl_server]
---
