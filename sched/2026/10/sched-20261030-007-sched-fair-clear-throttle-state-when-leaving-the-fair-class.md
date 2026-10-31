# sched/fair: Clear throttle state when leaving the fair class

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261023-003：Daehyeon Ko 发单补丁修 CFS 带宽节流的状态残留——任务迁出 fair 类时只把 `p->throttled` 从 `throttled_limbo_list` 移除却不**清位**，若期间最后一份有限配额被禁用、再回 fair 类会走真实 enqueue 却仍带 `throttled` 位，最终 fair picker 选中 `TASK_DEAD` 触发 `BUG()`。已获 Aaron Lu Reviewed-by。
- sched-20261029-008：维护者 Benjamin Segall 确认完整链路，并给出关键修正——应改用 `switched_from_fair` 清除，因为它覆盖 `TASK_ON_RQ_MIGRATING` 下行类切换跳过 `dequeue_task_fair` 的场景。
- sched-20261030-007（今天）：Benjamin Segall 复信「Right, of course, sigh. So then this should indeed be fine.」并给出 **Reviewed-By**——确认改用 `switched_from_fair` 清除 `->throttled` 的方向正确、可合入。

## 背景与问题
（承接 20261023-003 → 20261029-008）基于任务的 CFS 带宽节流在任务迁出 fair 类时残留 `p->throttled` 位，等信息被走私进 `!cfs_bandwidth_used()` 状态后造成 corruption。前一日已确认关键机理：`TASK_ON_RQ_MIGRATING` 下类切换会跳过 `dequeue_task_fair`，因此挂在 `DEQUEUE_CLASS` 分支上的清除到不了位。今日为维护者对修正方向的最终确认，无新背景。

## 技术方案
（承接 20261029-008 的「改挂 `switched_from_fair`」）用 `switched_from_fair` 这一既有触点在类切换出 fair 时清除 `p->throttled`，覆盖迁移中跳过 `dequeue_task_fair` 的情况。Benjamin Segall 今日确认该方向「should indeed be fine」——原「只在 `DEQUEUE_CLASS` 清除」的顾虑（会漏掉迁移场景）已解除。代码层面今日无新补丁，待作者按此方向出下一版。

## 版本演进与当前进展
*current_version: v1*（2026-10-22 首发；今日为维护者最终 Reviewed-by）。方向从「DEQUEUE_CLASS 清位」修正为「switched_from_fair 清位」，并获维护者认可，等待作者改版。

## Maintainer 意见与讨论焦点
- **Benjamin Segall（CFS maintainer）**：今日给出 **Reviewed-By**，确认改用 `switched_from_fair` 后修复正确。
- 无遗留分歧——此前 `TASK_ON_RQ_MIGRATING` 的覆盖问题已被该触点解决。

## 合入评估
*likelihood=high*。维护者已 Reviewed-by、方向与技术面均无异议，作者改版后即可合入。*blocking_issues*：仅剩作者按 `switched_from_fair` 方向发出修正版。*next_action*：作者发 v2（改用 switched_from_fair 清除），随后收取。

## 效果评估
无性能数据；修复目标为消除可触发 `BUG()` 的正确性缺陷（KASAN/LOCKDEP/DEBUG_LIST 下已复现）。

## 我可以参与的点
- **review**：作者发 v2 后，核对 `switched_from_fair` 中清除 `p->throttled` 与 `throttled_limbo_list` 移除的时序，确认无新竞态。
- **testing**：复跑作者此前的复现（CapPrm=CapEff=0 的委派场景）确认 no `BUG()`。

## 参考链接
- lore thread: https://lore.kernel.org/all/20261022235234.150957-1-4ncienth@gmail.com/

---
id: sched-20261030-007
date: 2026-10-30
subject: "sched/fair: Clear throttle state when leaving the fair class"
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: "<20261022235234.150957-1-4ncienth@gmail.com>"
lore_url: "https://lore.kernel.org/all/20261022235234.150957-1-4ncienth@gmail.com/"
authors: [Daehyeon Ko]
maintainers_involved: [Benjamin Segall]
current_version: v1
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "仅剩作者按 switched_from_fair 方向发出修正版（v2）"
  next_action: "作者发 v2（改用 switched_from_fair 清除 p->throttled），随后收取"
contribution_opportunities:
  - kind: review
    description: "核对 v2 中 switched_from_fair 清位与 throttled_limbo_list 移除的时序"
  - kind: testing
    description: "复跑 CapPrm=CapEff=0 委派复现场景，确认无 BUG()"
generated_at: "2026-10-31T09:00:00"
source_email_count: 1
related_articles: [sched-20261023-003, sched-20261029-008]
tags: [cfs]
---