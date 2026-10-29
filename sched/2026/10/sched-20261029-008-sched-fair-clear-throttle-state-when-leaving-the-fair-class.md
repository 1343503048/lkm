# sched/fair: Clear throttle state when leaving the fair class

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261023-003：Daehyeon Ko 发单补丁修 CFS 带宽节流的状态残留——任务从 fair 类迁出（`DEQUEUE_CLASS`）时只把 `p->throttled` 从 `throttled_limbo_list` 移除却不**清位**，若期间最后一份有限配额被禁用、再回 fair 类时会走真实 enqueue 却仍带 `throttled` 位，最终 `put_prev_task_fair()` 把实体放回 EEVDF 树、fair picker 选中 `TASK_DEAD` 任务触发 `BUG()`。已获 Aaron Lu `Reviewed-by`。
- sched-20261029-008（今天）：维护者 **Benjamin Segall** 确认了这条「走私 `->throttled` 到 `!cfs_bandwidth_used()` 再经 enqueue_throttled 检查把它真正 enqueue 导致 corruption」的完整链路，并给出关键修正：应改用 **`switched_from_fair`** 清除——因为当任务处于 `TASK_ON_RQ_MIGRATING` 时，类切换会**完全跳过 `dequeue_task_fair`**，根本看不到 `DEQUEUE_CLASS`；而对被节流任务触发迁移是确实可能发生的。K Prateek Nayak / Aaron Lu 就「类切换是否已被 `task_rq_lock()` 与迁移串行化」展开讨论。

## 背景与问题
（承接 20261023-003）基于任务的 CFS 带宽节流（task-based throttling）在任务被节流时移除其 fair `sched_entity`，但 `p->throttled` 这一 fair 专属状态会跨 dequeue/enqueue 存续。触发链（Benjamin Segall 今日确认）：类切换把 `->throttled` 走私进 `!cfs_bandwidth_used()` 状态，随后 enqueue_throttled 上的检查又把它走私成「真正 enqueue」，最终导致 corruption。今日新增的机理细节：**`TASK_ON_RQ_MIGRATING` 场景**——迁移中的任务做类切换时会跳过 `dequeue_task_fair`，所以 `DEQUEUE_CLASS` 分支根本不会执行。

## 技术方案
（承接 20261023-003 的「只在 `DEQUEUE_CLASS` 时清除 `p->throttled`」）今日方向修正：Benjamin Segall 认为应改用 **`switched_from_fair`** 这一既有触点来清除，因为它覆盖 `TASK_ON_RQ_MIGRATING` 下类切换跳过 `dequeue_task_fair` 的情况——否则对被节流任务触发迁移时（作者确信可发生），残留的 `throttled` 位仍会漏过去。作者原实现挂在 `DEQUEUE_CLASS` 上，该分支在迁移中不会走到。

## 版本演进与当前进展
*current_version: v1*（2026-10-22，`<20261022235234.150957-1-4ncienth@gmail.com>`）。今日无新补丁版本，是维护者对修复**落点**的修正讨论：从 `DEQUEUE_CLASS` 改为 `switched_from_fair`。作者尚未发出 v2。

## Maintainer 意见与讨论焦点
- **Benjamin Segall（维护者，Google）**：确认 corruption 链路成立（「smuggle ->throttled ... leads to corruption. That's fun.」）；明确建议「we need to use switched_from_fair」；指出「迁移一个被节流任务可以发生（I'm fairly sure）」，所以 `DEQUEUE_CLASS` 触点不够；遗憾不能复用现有触点但「at least it's trivial」。
- **K Prateek Nayak（AMD）**：指出 `task_rq_lock()` 在任务 `ON_RQ_MIGRATING` 时拿不到、而 `guard(sched_change)` 不该看到 `TASK_ON_RQ_MIGRATING`（类切换时任务要么完全 blocked 要么已 enqueue）。
- **Aaron Lu（bytedance，v1 的 Reviewed-by）**：认为类切换已与迁移串行化（`task_rq_lock()` 等待迁移 settle），质疑该场景是否真会出现。
- 未解决焦点：`TASK_ON_RQ_MIGRATING` 下类切换是否真会跳过 `dequeue_task_fair`——Ben 认为会、Aaron Lu 认为不会，需作者按 `switched_from_fair` 落点重发后收敛。

## 合入评估
*likelihood=high*。维护者 Benjamin Segall 直接介入并给出明确修法（`switched_from_fair`），方向无异议、改动 trivial；Aaron Lu 的 v1 `Reviewed-by` 对旧落点有效，新落点需重新 review。*blocking_issues*：作者尚未按 `switched_from_fair` 重发 v2；`TASK_ON_RQ_MIGRATING` 机理争议需在 v2 里说明。*next_action*：作者改到 `switched_from_fair` 触点重发 v2，附上迁移中被节流任务的论证。

## 效果评估
无性能数据——这是正确性修复。作者 v1 曾在 KASAN/LOCKDEP/DEBUG_LIST 的 v7.3 内核以 CapPrm=CapEff=0 复现（3/3 root、3/3 委派），即 `do_task_dead()` → `BUG()` 崩溃。今日讨论聚焦机理与修法落点，无新复现数据。

## 我可以参与的点
- **review**：核对「`TASK_ON_RQ_MIGRATING` 下类切换是否跳过 `dequeue_task_fair`」这条 Ben 与 Aaron Lu 的分歧点（`sched_core` 的 `sched_change` 路径），帮作者在 v2 里给出严谨论证。
- **testing**：在启用 task-based cgroup 带宽节流的环境下，构造「节流中触发迁移 + 类切换」场景验证 v2（`switched_from_fair` 落点）不再残留 `throttled`。

## 参考链接
- lore thread（v1 补丁）: https://lore.kernel.org/all/20261022235234.150957-1-4ncienth@gmail.com/
- Benjamin Segall 的修正建议: https://lore.kernel.org/all/xm26ecd9ihv8.fsf@google.com/
- K Prateek Nayak 的讨论: https://lore.kernel.org/all/725e7cc3-711c-4afd-8fb0-78f79d45de7d@amd.com/

---
id: sched-20261029-008
date: 2026-10-29
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
patch_series:
  - version: v1
    msgid: "<20261022235234.150957-1-4ncienth@gmail.com>"
    date: 2026-10-22
    summary: "单补丁：只在 DEQUEUE_CLASS 时清除 p->throttled，避免 fair 专属状态在离开 fair 类后残留"
    review_outcome: "Aaron Lu Reviewed-by；今日 Benjamin Segall 建议改用 switched_from_fair 落点"
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
    - "作者需按 switched_from_fair 落点重发 v2"
    - "TASK_ON_RQ_MIGRATING 下类切换是否跳过 dequeue_task_fair 的机理需在 v2 论证"
  next_action: "作者改到 switched_from_fair 触点重发 v2 并附迁移中被节流任务的论证"
contribution_opportunities:
  - kind: review
    description: "核对 TASK_ON_RQ_MIGRATING 下类切换是否跳过 dequeue_task_fair，帮作者论证"
  - kind: testing
    description: "构造节流中迁移 + 类切换场景验证 v2 不再残留 throttled"
generated_at: "2026-10-30T09:30:00"
source_email_count: 3
related_articles: [sched-20261023-003]
tags: [cfs]
---