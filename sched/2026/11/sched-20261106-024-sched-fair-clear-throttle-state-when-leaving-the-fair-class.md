# sched/fair: Clear throttle state when leaving the fair class

## TL;DR

Daehyeon Ko 的修复今日合入 tip/sched/urgent（commit `c282051fc2cae2ea54770ebe435dbea090272c25`，Cc: stable）：任务迁出 fair 类时只在 `throttled_limbo_list` 移除 `p->throttled` 却不清位，若期间最后一份有限 CFS 配额被禁用、再回 fair 类会走真实 enqueue 却仍带 `throttled` 位，最终 fair picker 选中 `TASK_DEAD` 任务触发 `do_task_dead()` 的 BUG()。修复让 `DEQUEUE_CLASS` 也清除 `p->throttled`。此前经维护者 Benjamin Segall 确认并获 Aaron Lu Reviewed-by。

## 背景与问题

task-based CFS 带宽节流：任务迁出 fair 类时 `DEQUEUE_CLASS` 只把 `p->throttled` 从 `throttled_limbo_list` 摘除、保留其位。若此时最后一份有限配额被禁用，任务不在 unthrottle walk 里、位残留；回到 fair 类且 `cfs_bandwidth_used()` 为 false 时做的是真实 enqueue 却仍带 `throttled` 位。带宽重新启用后，class-change dequeue 把 stale 位当 limbo 状态、跳过 `__dequeue_task()`，`se.on_rq` 残留、`put_prev_task_fair()` 把实体放进 EEVDF 树——任务已迁往 RT 却在树里，退出时 fair picker 选中 `TASK_DEAD`，`__schedule()` 返回 `do_task_dead()` 触发 BUG()。

## 技术方案

`dequeue_throttled_task()` 的条件从 `DEQUEUE_SLEEP` 扩展到 `DEQUEUE_SLEEP | DEQUEUE_CLASS`，即迁出 fair 类时也清 `p->throttled`（fair 专属状态不应存活于 fair 类之外）。改动 `kernel/sched/fair.c` +2/-2 行。

## 版本演进与当前进展

*current_version: v1（2026-10-23 发出）*。10 月经 Benjamin Segall 确认完整链路（应改用 `switched_from_fair` 覆盖 TASK_ON_RQ_MIGRATING 路径）后给 Reviewed-By、Aaron Lu Reviewed-by。今日合入 tip/sched/urgent，Cc: stable。

## Maintainer 意见与讨论焦点

Benjamin Segall（sched 维护者）确认方向并 Review；Aaron Lu Reviewed-by。提交说明含 KASAN/LOCKDEP/DEBUG_LIST v7.3 下 3/3 root 与 3/3 delegated 复现与修复后全绿。无异议。

## 合入评估

*likelihood=merged*。已进 tip/sched/urgent，commit `c282051fc2cae2ea54770ebe435dbea090272c25`。*blocking_issues*：无。*next_action*：随 sched/urgent 进入主线并回合 stable。

## 效果评估

提交说明：v7.3 + KASAN/LOCKDEP/DEBUG_LIST 下 `do_task_dead()` BUG 在 3/3 root 与 3/3 delegated uid-1000 运行中稳定复现；修复后两套矩阵 + 带宽持续的 class-switch 对照组全过，无调度告警/KASAN/lockdep/crash。

## 我可以参与的点

当前阶段无参与空间（已合入）。

## 参考链接

- tip commit: https://git.kernel.org/tip/c282051fc2cae2ea54770ebe435dbea090272c25
- 原补丁 lore: https://patch.msgid.link/20261022235234.150957-1-4ncienth@gmail.com

---
id: sched-20261106-024
date: 2026-11-06
subject: "sched/fair: Clear throttle state when leaving the fair class"
subsystem: sched
type: fix
status: merged_tip
severity: high
thread_root_msgid: "<179395863813.1009794.9427104434880401809.tip-bot2@tip-bot2>"
lore_url: "https://lore.kernel.org/all/179395863813.1009794.9427104434880401809.tip-bot2@tip-bot2/"
authors: [Daehyeon Ko]
maintainers_involved: [Ingo Molnar, Peter Zijlstra]
current_version: v1
patch_series:
  - version: v1
    msgid: "<20261022235234.150957-1-4ncienth@gmail.com>"
    date: 2026-10-23
    summary: "DEQUEUE_CLASS 也清 p->throttled，避免 class 切换后 BUG()。"
    review_outcome: "Benjamin Segall/Aaron Lu Reviewed-by；11-06 合入 tip/sched/urgent。"
upstream_commit: "c282051fc2cae2ea54770ebe435dbea090272c25"
fixes_commit: "e1fad12dcb66"
merged_branch: "tip/sched/urgent"
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: "随 sched/urgent 进入主线并回合 stable"
contribution_opportunities: []
generated_at: "2026-11-07T09:00:00+08:00"
source_email_count: 1
related_articles: [sched-20261030-007]
tags: [cfs, cgroup]
---