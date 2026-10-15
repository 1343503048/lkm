# sched_ext: Wait for SCX_OPSS_DISPATCHING on DSQ consume and move paths

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261013-006：Kuba Piecuch 发 2 补丁修复（挂 `sched_ext/for-7.3-fixes`）：任务可在「调度它的 CPU 仍在跑 `ops.dequeue()`、尚未清 `SCX_OPSS_DISPATCHING`」时就被发现在非本机 DSQ 上，DSQ 的 consume/move 路径不等 dispatch 完成、会与 dispatcher 并发操作同一任务；系列在关键路径补 `scx_wait_dispatching()`，Andrea Righi 双 `Reviewed-by`，`Cc: stable # v7.1+`。
- sched-20261015-022（今天）：Tejun Heo 已把 1-2 应用到 `sched_ext/for-7.3-fixes`（补 Andrea 的 Reviewed-by，并把 `unlink_dsq_and_switch_rq_lock()` 里 `holding_cpu` 条件合并成一行）。

## 背景与问题
（承接 20261013-006）dispatch 落到非本机 DSQ 时，`scx_dispatch_enqueue()` 链入 DSQ 后（对 global/bypass DSQ）在**不持任务 rq 锁**的情况下调 `ops.dequeue()`，之后才写 `SCX_OPSS_NONE`；`ebf1ccff79c4` 与 `cb86607ada73` 两次重构后，任务可在仍处 `SCX_OPSS_DISPATCHING` 时就被发现在 DSQ 上，consume/move 路径与 dispatcher 并发操作同一任务。

## 技术方案
（承接 20261013-006）两补丁：Patch 1 把 `scx_reenq_wait_dispatching()` 改名 `scx_wait_dispatching()`；Patch 2 在 `scx_move_local_task_to_local_dsq()`、`unlink_dsq_and_switch_rq_lock()`、`move_task_between_dsqs()` 三处操作任务前先 `scx_wait_dispatching(p)`。今日 Tejun 应用时把 `unlink_dsq_and_switch_rq_lock()` 中 `holding_cpu` 条件合并一行（无功能变化）。

## 版本演进与当前进展
- 1-2 补丁（2026-10-12，<20261012210749.2955291-1-jpiecuch@google.com>）→ 今日 Tejun 应用进 `sched_ext/for-7.3-fixes`。

## Maintainer 意见与讨论焦点
Tejun Heo 已应用，Andrea Righi 已 Reviewed-by；无争议。

## 合入评估
*likelihood=merged*。已应用到 `sched_ext/for-7.3-fixes`（将随 sched_ext fixes 进 v7.3 stable）。*blocking_issues*：无。*next_action*：随 sched_ext for-7.3-fixes 汇总进 v7.3-rc/stable。

## 效果评估
无量化数据，属并发正确性修复。

## 我可以参与的点
当前阶段暂无明显参与空间，已合入 fixes 分支。

## 参考链接
- Tejun 的应用确认：https://lore.kernel.org/all/297ee1a03ba086fe0afd29e7a1e89367@kernel.org/
- 原始系列：https://lore.kernel.org/all/20261012210749.2955291-1-jpiecuch@google.com/

---
id: sched-20261015-022
date: 2026-10-15
subject: "sched_ext: Wait for SCX_OPSS_DISPATCHING on DSQ consume and move paths"
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: "<20261012210749.2955291-1-jpiecuch@google.com>"
lore_url: "https://lore.kernel.org/all/20261012210749.2955291-1-jpiecuch@google.com/"
authors: ["Kuba Piecuch"]
maintainers_involved: ["Tejun Heo"]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261012210749.2955291-1-jpiecuch@google.com>"
    date: 2026-10-12
    summary: "2 补丁：改名 scx_wait_dispatching + 关键路径补等待"
    review_outcome: "Andrea Reviewed-by；Tejun 今日应用进 for-7.3-fixes"
upstream_commit: null
fixes_commit: null
merged_branch: "sched_ext/for-7.3-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched_ext for-7.3-fixes 进 v7.3 stable"
contribution_opportunities: []
generated_at: "2026-10-16T01:05:00"
source_email_count: 1
related_articles: ["sched-20261013-006"]
tags: [sched_ext]
---