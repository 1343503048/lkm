# sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- sched-20261024-001（v33）：John Stultz 的 proxy execution 第 5 阶段「Sleeping Owner Handling」第 33 版，扩到 7 补丁，聚合多人修复（psi 状态、远程 tick 用 rq->donor、无 owner 激活 blocked donor、proxy 链循环检测等）；Peter Zijlstra、Andrea Righi、Kayra Cizmeci 当日密集 review。
- sched-20261026-006：7/7 核心补丁及 1/3/4 补丁的深度 review。
- sched-20261027-010（今天）：Kayra Cizmeci 对 7/7 补丁再提一条 review：质疑 `find_proxy_task()` 里「deactivated（sleeping）owner」的处理是否也需覆盖 delayed 任务，并给出 `proxy_enqueue_on_owner()` → `block_task()` → `dequeue_task_fair()` 可能只置 `sched_delayed`、不停用任务的具体链路。

## 背景与问题
（承接 v32/v33）proxy execution 第 5 阶段处理「任务阻塞在 mutex 上而 owner 本身在睡眠」：需在 owner 唤醒时重新激活挂在其上的 waiter 树，waiters 还可嵌套、需额外列表规避级联递归。7/7 补丁给 `find_proxy_task()` 加 deactivated（sleeping）owner 的查找处理。

## 技术方案
（承接 v33）7/7 补丁内容为在 `find_proxy_task()` 中处理已停用的睡眠 owner。今日无代码变更；Kayra 提出一个潜在的覆盖面问题：delayed 任务可能也会走到 `find_proxy_task()`，而当前处理可能只覆盖 `is_blocked`（on owner list）而非 `sched_delayed` 的任务。

## 版本演进与当前进展
*current_version: v33*（`<20261023220431.1106611-8-jstultz@google.com>`）。今日 7/7 再收一条 review。

## Maintainer 意见与讨论焦点
Kayra Cizmeci 对 7/7 的 nit（指代 'her'）及一个实质问题：`proxy_enqueue_on_owner()` 把任务挂到 owner list 后调 `block_task()`，若任务不 eligible 则只置 `sched_delayed=1` 而 `__block_task()` 未执行（返回 false），此时任务 on_rq 且在 owner list；owner 唤醒时 `do_activate_blocked_waiter()` 跳过 delayed 任务——作者怀疑 `find_proxy_task()` 的 deactivated-owner 处理也应覆盖这类 delayed 任务。该问题今日尚未得到 John Stultz 回应。

## 合入评估
*likelihood=medium*（针对 7/7 当前形态；整系列 v33 已离合入不远，但 Peter 尚未放行）。*blocking_issues*：Kayra 的 delayed 任务覆盖面疑问待作者回应。*next_action*：John Stultz 回应 Kayra 的 delayed 任务疑问后，等 Peter 对整系列表态。

## 效果评估
无性能数据。正确性修复系列，靠 review 收敛。

## 我可以参与的点
- *kind: review*：核对 delayed 任务与 deactivated owner 在 `find_proxy_task()` 的交互，判断 Kayra 描述链路是否成立。

## 参考链接
- 7/7 patch: https://lore.kernel.org/all/20261023220431.1106611-8-jstultz@google.com/
- v33 cover: https://lore.kernel.org/all/20261023220431.1106611-1-jstultz@google.com/

---
id: sched-20261027-010
date: 2026-10-27
subject: 'sched/proxy: Add deactivated (sleeping) owner handling to find_proxy_task()'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: '<20261023220431.1106611-8-jstultz@google.com>'
lore_url: 'https://lore.kernel.org/all/20261023220431.1106611-8-jstultz@google.com/'
authors:
  - 'John Stultz'
maintainers_involved: []
current_version: v33
patch_series:
  - version: v33
    msgid: '<20261023220431.1106611-8-jstultz@google.com>'
    date: 2026-10-23
    summary: '7 patches，含 7/7 deactivated (sleeping) owner 处理'
    review_outcome: 'Kayra 对 7/7 提 delayed 任务覆盖面疑问'
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
    - 'Kayra 的 delayed 任务覆盖面疑问待回应'
  next_action: 'John Stultz 回应 delayed 任务疑问后等 Peter 表态'
contribution_opportunities:
  - kind: review
    description: '核对 delayed 任务与 deactivated owner 在 find_proxy_task() 的交互'
generated_at: '2026-10-28T09:00:00'
source_email_count: 1
related_articles:
  - sched-20261024-001
  - sched-20261025-010
  - sched-20261026-006
tags:
  - proxy_execution
---