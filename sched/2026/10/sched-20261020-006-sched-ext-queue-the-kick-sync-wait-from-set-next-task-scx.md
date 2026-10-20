# sched_ext: Queue the kick_sync wait from set_next_task_scx()

## TL;DR

本文为增量更新，完整脉络见下。

- sched-20261018-006：Andrea Righi 发 `Fix scx balance callbacks queued across a core-sched pick`（2 补丁）修复 ff0545e0c263 遗留的 core-sched 缺口；1/2 被 Tejun 应用到 `sched_ext/for-7.3-fixes`；2/2（kick_sync wait）Tejun 建议改到 for-7.4 按「从 set_next_task_scx() 排队」做。
- sched-20261019-001：Andrea 发 v2 单补丁落实——把 kick_sync wait 移到 `set_next_task_scx()` 的 SNT_PICK/SNT_REPICK 排队，`kick_sync_pending` 在 callback 运行时清除。
- sched-20261020-006（今天）：Tejun 应用本 v2 到 `sched_ext/for-7.4-fixes`，并附三个 follow-up：proxy exec 下 `__schedule()` 会对 repicked donor 调两次 `set_next_task()`（SNT_REPICK→SNT_PICK）导致 `kick_sync_bal_cb` 排队两次、自链后 wait 跑两次；`kick_sync_wait_bal_cb()` 的 foreign CPU check 现已不可达；`maybe_queue_balance_callback()` 排队时清 `SCX_RQ_BAL_CB_PENDING`，proxy exec zap 会让 deferred work 悬置到下次 wakeup/deferred 请求。

## 背景与问题

（承接 20261018-006 → 20261019-001）SCX_KICK_WAIT wait 被推迟到 `rq->scx.kick_sync_bal_cb`，由最后一次 pick 在本地 rq 排队。core scheduling 下「返回任务的 pick」非终态，`pick_next_task()` 会继续挑 SMT sibling，sibling 的 dispatch 可能在 callback 仍排队时释放共享 rq 锁，触发 `rq_pin_lock()` WARNING。v2 把排队移到 `set_next_task_scx()` 的 SNT_PICK/SNT_REPICK（`put_prev_set_next_task()` 在 pick 最终确定后才调用它），并把 `kick_sync_pending` 改到 callback 运行时清除。今天 Tejun 收取该 v2。

## 技术方案

（承接，今日为合入 + follow-up）v2 单补丁（`kernel/sched/ext/`）：从 `set_next_task_scx()` 的 SNT_PICK/SNT_REPICK 排队 kick_sync wait，`kick_sync_pending` 在 callback 运行时清除。Tejun 已应用到 `sched_ext/for-7.4-fixes`。

Tejun 顺带提出三个 follow-up（非本补丁阻塞项）：
- proxy exec 下 `__schedule()` 可对 repicked donor 调两次 `set_next_task()`（SNT_REPICK 再 SNT_PICK），把 `kick_sync_bal_cb` 排队两次；当其是 list 上唯一节点时会自链、wait 跑两次。
- `kick_sync_wait_bal_cb()` 里的 foreign CPU check 现在看不可达。
- `maybe_queue_balance_callback()` 排队时会清 `SCX_RQ_BAL_CB_PENDING`，所以 proxy exec zap 留下的 deferred work 会直到下次 wakeup 或 deferred 请求才被排上。

## 版本演进与当前进展

*current_version: v2*（已应用）。

- v1（20261018-006 的 2/2）：dispatch 前取下/必要时再排队。
- v2（20261019-001，`<20261018162415.55913-1-arighi@nvidia.com>`）：改到 `set_next_task_scx()` 排队、`kick_sync_pending` 在 callback 运行时清除。
- 今日：Tejun 应用到 `sched_ext/for-7.4-fixes`。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）今日收取 v2（`Applied to sched_ext/for-7.4-fixes`），无分歧。同时给出三个 follow-up 观察（proxy exec 双重 set_next_task、不可达 foreign CPU check、balance callback pending 被清），属于后续需处理的边界问题，不影响本次合入。

## 合入评估

*likelihood=merged*。v2 已由 Tejun 应用到 `sched_ext/for-7.4-fixes`。*blocking_issues*：无（本系列已合入）。*next_action*：跟进 Tejun 的三个 follow-up（proxy exec 双重排队、不可达 check、balance callback pending），判断是否需要后续补丁。

## 效果评估

无量化数据，属正确性修复。前作（20261018-006）给出复现：仅 ff0545e0c263 时 debug 检查 10 次中 5 次触发 WARNING，加 1/2 后 16 次 0 触发；v2 未附新增测试数据。

## 我可以参与的点

- `new_patch`：Tejun 指出的「proxy exec 下 `__schedule()` 对 repicked donor 两次 `set_next_task()` 导致 `kick_sync_bal_cb` 自链、wait 跑两次」是明确的后续修复点，可跟进发补丁。
- `review`：复核 `kick_sync_wait_bal_cb()` 的 foreign CPU check 是否确已不可达、以及 `maybe_queue_balance_callback()` 清 `SCX_RQ_BAL_CB_PENDING` 的时机在 proxy exec zap 下的影响。

## 参考链接

- Tejun 今日回帖（Applied + follow-ups）：https://lore.kernel.org/all/08cac02c604dd73ef96fc92eb29d692b@kernel.org/
- v2 patch：https://lore.kernel.org/all/20261018162415.55913-1-arighi@nvidia.com/

---
id: sched-20261020-006
date: 2026-10-20
subject: "sched_ext: Queue the kick_sync wait from set_next_task_scx()"
subsystem: sched
type: fix
status: merged_tip
severity: medium
thread_root_msgid: "<20261018162415.55913-1-arighi@nvidia.com>"
lore_url: "https://lore.kernel.org/all/20261018162415.55913-1-arighi@nvidia.com/"
authors: ["Andrea Righi"]
maintainers_involved: ["Tejun Heo"]
current_version: v2
patch_series:
  - version: v1
    msgid: "<20261017202025.3834954-1-arighi@nvidia.com>"
    date: 2026-10-18
    summary: "core-sched 掉锁修复（1/2）+ kick_sync wait 在 dispatch 前取下/必要时再排队（2/2）"
    review_outcome: "1/2 应用 for-7.3-fixes；2/2 Tejun 建议改 set_next_task_scx() 排队并放 for-7.4"
  - version: v2
    msgid: "<20261018162415.55913-1-arighi@nvidia.com>"
    date: 2026-10-19
    summary: "从 set_next_task_scx() 的 SNT_PICK/SNT_REPICK 排队 kick_sync wait；kick_sync_pending 在 callback 运行时清除"
    review_outcome: "Tejun 应用到 sched_ext/for-7.4-fixes，附三个 follow-up"
upstream_commit: null
fixes_commit: "415cb193bb97"
merged_branch: "sched_ext/for-7.4-fixes"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "跟进 Tejun 的三个 follow-up（proxy exec 双重排队、不可达 check、balance callback pending）"
contribution_opportunities:
  - kind: new_patch
    description: "修复 proxy exec 下 __schedule() 两次 set_next_task 导致 kick_sync_bal_cb 自链的问题"
  - kind: review
    description: "复核 kick_sync_wait_bal_cb() foreign CPU check 是否不可达及 BAL_CB_PENDING 清理时机"
generated_at: "2026-10-21T01:30:00"
source_email_count: 1
related_articles: ["sched-20261010-009", "sched-20261015-020", "sched-20261017-002", "sched-20261018-006", "sched-20261019-001"]
tags: [sched_ext, core_sched]
---