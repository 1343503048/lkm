---
id: sched-20261112-004
date: '2026-11-12'
subject: 'sched/fair: Avoid transient double accounting for delayed tasks'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
lore_url: https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/
authors:
- K Prateek Nayak
maintainers_involved:
- Vincent Guittot
- Peter Zijlstra
current_version: v1
patch_series:
- version: v1
  msgid: <20261112083447.25603-1-kprateek.nayak@amd.com>
  date: '2026-11-12'
  summary: 去除 delayed 任务 dequeue 的瞬态 double accounting，并为非法 ENQUEUE_WAKEUP 组合加告警
  review_outcome: Vincent Reviewed-by；Peter 正面认可
upstream_commit: null
fixes_commit: 85570f10a4c6
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等 Peter/Ingo 收取进 tip/sched/urgent
contribution_opportunities:
- kind: testing
  description: 复现早期启动 WARN_ON_ONCE 并确认补丁后消失
- kind: review
  description: 核对 ENQUEUE_WAKEUP && sched_delayed 告警分支是否误报
generated_at: '2026-11-13T09:00:00+08:00'
source_email_count: 3
related_articles: []
tags:
- eevdf
- cfs
title: 'sched/fair: Avoid transient double accounting for delayed tasks'
layout: article
---

## TL;DR

K Prateek Nayak 修一个 delayed-dequeue 记账缺陷：任务被 delay 时 `set_delayed()` 调整了 `h_nr_runnable`，但带 `DEQUEUE_DELAYED` 的 dequeue 又在 `dequeue_hierarchy()` 里再减一次（随后 `__dequeue_task()` 经 `clear_delayed()` 立刻纠正），导致早期启动阶段可靠触发 `WARN_ON_ONCE(h_nr_runnable < 0)`，且这个短暂错误值会被缓存进 `se->runnable_weight` 影响 PELT。Vincent Guittot 已给 Reviewed-by，Peter Zijlstra 回「Urgh, thanks!」。合入可能性高。

## 背景与问题

`Fixes: 85570f10a4c6 ("sched/eevdf: Move to a single runqueue")`。单 runqueue 化之后，delayed 任务（`DEQUEUE_DELAYED`）在 dequeue 路径里存在一次「先多减、再纠正」的瞬时双记账：`set_delayed()` 已经把 `h_nr_runnable` 调整掉，`dequeue_hierarchy()` 又把 `cfs_rq->h_nr_runnable` 减一次，直到 `__dequeue_task()` 里 `clear_delayed()` 才把它加回来。作者在 `dequeue_hierarchy()` 的记账之后加 `WARN_ON_ONCE(((int)cfs_rq->h_nr_runnable) < 0)`，早期启动阶段可靠 tripped。虽然只是瞬态，但这个错误值会被缓存进 `se->runnable_weight` 并影响 PELT 计算，直到下一次 enqueue/dequeue 才被纠正。另一处：任务唤醒（`ENQUEUE_WAKEUP && se->sched_delayed`）本不该走到 `enqueue_hierarchy()`，唤醒 delayed 任务必须耦合 `ENQUEUE_DELAYED`（在 `enqueue_task_fair()` 里正确处理）。

## 技术方案

单补丁（`kernel/sched/fair.c` +27/-34）：在 `__dequeue_task()` 里避免错误的 `h_nr_runnable` 记账；并为「delayed 任务只带 `ENQUEUE_WAKEUP` 就走到 enqueue」这一应属非法的唤醒 flag 组合加告警。净效果是删掉 7 行冗余/易错逻辑，让 delayed 任务的 dequeue/enqueue 记账只在正确路径发生一次。

## 版本演进与当前进展

*current_version: v1（2026-11-12，`<20261112083447.25603-1-kprateek.nayak@amd.com>`）*。当日发出，无版本演进。

## Maintainer 意见与讨论焦点

- **Vincent Guittot（sched/fair 维护者）**：`Reviewed-by`。
- **Peter Zijlstra**：「Urgh, thanks!」——认可方向（语气带「这种坑早就该修」的意味），未提实质异议。
- 无 NAK、无未解决分歧。

## 合入评估

*likelihood=high*。已获 sched/fair 维护者 Vincent Guittot 的 Reviewed-by，Peter 亦正面表态，且是带 `Fixes:` 的正确性修复。*blocking_issues*：无。*next_action*：等 Peter 或 Ingo 收取进入 tip/sched/urgent（作者已标 Fixes 单 runqueue 化提交）。

## 效果评估

作者未给量化数据；收益为消除可复现的 `WARN_ON_ONCE` 告警与瞬态 `runnable_weight` 污染（影响 PELT），属记账正确性修复。

## 我可以参与的点

- **testing**：在启用 DELAY_DEQUEUE 的 EEVDF 内核上复现早期启动的 `WARN_ON_ONCE(h_nr_runnable < 0)`，确认补丁后消失、PELT 不再被瞬态污染。
- **review**：核对 `ENQUEUE_WAKEUP && sched_delayed` 的告警分支是否可能误报（是否存在合法路径只带 ENQUEUE_WAKEUP 唤醒 delayed 任务）。

## 参考链接

- lore thread: https://lore.kernel.org/all/20261112083447.25603-1-kprateek.nayak@amd.com/
- Vincent 的 Reviewed-by: https://lore.kernel.org/all/CAKfTPtDgksPa3uRESu2dLc55b-Wya5TXxg0b_DiQNKe5Fy=KkQ@mail.gmail.com/
