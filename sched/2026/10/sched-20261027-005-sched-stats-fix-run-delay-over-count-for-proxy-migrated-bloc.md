# sched/stats: Fix run_delay over-count for proxy-migrated blocked donors

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261025-002（v1）：Wei Yang 补发单补丁，修 proxy execution 下被迁移的 blocked donor 的 run_delay 多计：`find_proxy_task()` 把仍在阻塞的 donor 迁到 owner 的 CPU 时，`activate_task(ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-arm 了 `last_queued`，阻塞时长被误算成等 CPU 时长；补丁新增 `!task_is_blocked()` 门控，2 CPU VM 实测 ~170ms 阻塞从 ~167ms 降到 0.01ms。
- sched-20261026-001：Kayra 与 K Prateek 密集 review，K Prateek 提议反向思路（sched info 全面改用 `p->is_blocked` 单一判据）。
- sched-20261027-005（今天）：Peter Zijlstra 确认方向，并指出还有 `ttwu_runnable()` 与 `ttwu()` 顶部 `p==current` 两个非 enqueue 路径也需补 `sched_info_enqueue()`；K Prateek 给出 `proxy_needs_return()` 放置方案；Kayra 反例继续。

## 背景与问题
（承接 20261025-002）proxy exec（v7.1 合入）下任务阻塞在内核 mutex 上（proxy donor），其 mutex owner 在另一 CPU 运行。`find_proxy_task()` 经 `proxy_migrate_task()` 把仍阻塞的 donor 迁到 owner 的 CPU，该迁移用 `activate_task(rq, p, ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-attach donor，`sched_info_enqueue()` re-arm `last_queued` 尽管 donor 根本不 runnable——一次「假 enqueue」，导致 `run_delay`（等 CPU 时长）把阻塞时长一并计入。

## 技术方案
（承接 v1）核心仍是「任务仍阻塞在 mutex 上时不再 re-arm `last_queued`」（`!sched_delayed && !task_is_blocked()` 门控）。今日聚焦三处「不经 enqueue_task」却会开始等 CPU 计时的路径，需补 `sched_info_enqueue()`：

- **ttwu_runnable()**：真实唤醒不重走 enqueue_task，需在 `wakeup_preempt()` 分支补 `sched_info_enqueue(rq, p)`（Peter 确认、K Prateek 给完整 diff）。
- **proxy_needs_return()**：`task_cpu(p) == p->wake_cpu` 时在标记 `!is_blocked` 之前开始 wait 计时。
- **ttwu() 顶部 `p==current`**：Peter 指出第三个同样不经 enqueue_task 的点。

Kayra 指出 `proxy_needs_return()` 方案的边界：donor 与 owner 分处两 CPU、donor 回 home 后 owner 突然 drop mutex 时不做 dequeue，`is_blocked` 已清，计时不会被重置，会多算 mutex 等待+自身等待。

## 版本演进与当前进展
*current_version: v1*（`<20261025130740.3324391-1-albin_yang@163.com>`）。今日无新补丁版本，为设计/放置的密集讨论。

## Maintainer 意见与讨论焦点
Peter Zijlstra 认可方向，逐一确认三个需补 `sched_info_enqueue()` 的路径（ttwu_runnable、proxy_needs_return、ttwu 的 p==current）。K Prateek Nayak 提议把 `sched_info_dequeue/enqueue` 全面改用 `p->is_blocked` 单一判据（类比 PSI 信号处理），并给出 `proxy_needs_return()` 处补 enqueue 的 diff。分歧点：Kayra 认为 `proxy_needs_return()` 方案在「donor 回 home 后 owner 突然 drop mutex」场景会多算，倾向用 `is_blocked` 判定更干净，但该判定自身也有一处反例待澄清。

## 合入评估
*likelihood=medium*。方向无异议、属正确性修复，但三个计时点 + 是否统一 `is_blocked` 判据尚未收敛，作者需再出一版覆盖全部路径。*blocking_issues*：`proxy_needs_return()` 边界反例未闭环、ttwu p==current 点未落补丁。*next_action*：作者汇总三处计时点、回应 Kayra 反例后发 v2。

## 效果评估
v1 实测：2 CPU VM，同 ~170ms 阻塞从 ~167ms 降到 0.01ms（作者提供）。今日无新数据。

## 我可以参与的点
- *kind: review*：核实 `proxy_needs_return()` 在「donor 回 home 后 owner drop mutex」场景的计时归属是否正确。
- *kind: new_patch*：若倾向 `is_blocked` 单一判据方案，可协助把该 refactor 铺完整并压测三处路径。

## 参考链接
- 线程: https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/

---
id: sched-20261027-005
date: 2026-10-27
subject: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: '<20261025130740.3324391-1-albin_yang@163.com>'
lore_url: 'https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/'
authors:
  - 'Wei Yang'
maintainers_involved:
  - 'Peter Zijlstra'
current_version: v1
patch_series:
  - version: v1
    msgid: '<20261025130740.3324391-1-albin_yang@163.com>'
    date: 2026-10-25
    summary: '任务仍阻塞时不再 re-arm last_queued（!sched_delayed && !task_is_blocked()）'
    review_outcome: 'Peter 确认方向，指出还需补 ttwu_runnable 与 ttwu p==current 两处计时'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'proxy_needs_return() 边界反例未闭环'
    - 'ttwu() p==current 计时点未落补丁'
  next_action: '作者汇总三处计时点并回应 Kayra 反例后发 v2'
contribution_opportunities:
  - kind: review
    description: '核实 proxy_needs_return() 在 donor 回 home 后 owner drop mutex 场景的计时归属'
  - kind: new_patch
    description: '协助铺完 is_blocked 单一判据 refactor 并压测三处路径'
generated_at: '2026-10-28T09:00:00'
source_email_count: 8
related_articles:
  - sched-20261025-002
  - sched-20261026-001
tags:
  - proxy_execution
---