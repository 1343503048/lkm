---
id: sched-20260925-001
date: 2026-09-25
subject: 'sched: Restart fair hrtick after same-task repicks'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <179033365349.2819794.3113821108284833728.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033365349.2819794.3113821108284833728.tip-bot2@tip-bot2/
upstream_commit: c72945693b90423f1b46ac2dbc8749c2b7804fc8
fixes_commit: null
merged_branch: tip/sched/core
current_version: v4
generated_at: '2026-09-26T01:15:00'
authors:
- Shubhang Kaushik (Ampere)
maintainers_involved:
- Peter Zijlstra
patch_series:
- version: v1
  msgid: <20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>
  date: 2026-08-13
  summary: 重启 fair hrtick 的首版
  review_outcome: 暂无记录
- version: v2
  msgid: <20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>
  date: 2026-09-11
  summary: 用 SNT_REPICK 取代 fair 专用状态，fair/DL 都重启
  review_outcome: 无
- version: v3
  msgid: <20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>
  date: 2026-09-15
  summary: 移除 SCHED_DEADLINE 的 SNT_REPICK 重启
  review_outcome: 获 Zhan Xusheng Reviewed-by
- version: v4
  msgid: <20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org>
  date: 2026-09-17
  summary: 澄清 fair/DL 重启差异原因，文档化 SNT_* 调用点语义
  review_outcome: 09-25 Peter 以 v4 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities:
- kind: review
  description: 自家分支若用 CONFIG_SCHED_HRTICK，回合时需一并带回 SNT_REPICK 回调语义，注意与 v14 proxy-exec
    系列 SNT_CONFIRM 的相邻关系
source_email_count: 1
related_articles:
- sched-20260918-002
- sched-20260917-005
- sched-20260916-017
tags:
- cfs
- deadline
- preempt
title: 'sched: Restart fair hrtick after same-task repicks'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-002-sched-restart-fair-hrtick-after-same-task-repicks.html">sched-20260918-002</a> / <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-005-sched-restart-fair-hrtick-after-same-task-repicks.html">sched-20260917-005</a> / <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-017-sched-restart-fair-hrtick-after-same-task-repicks.html">sched-20260916-017</a>。Shubhang Kaushik (Ampere) 的「同一任务重新选中的 same-task repick 之后重启 fair hrtick」修复（v4）已被 Peter Zijlstra 合入 tip/sched/core（commit c72945693b90423f1b46ac2dbc8749c2b7804fc8，09-25 12:45:57 +0200），无更高版本。

## 背景与问题

Fair hrtick 是一次性（one-shot）定时器。hrtick 到期触发抢占请求后，若 `pick_next_task()` 又选中了**同一个任务**（same-task repick），`put_prev_set_next_task()` 会走 `next == prev` 路径直接返回，跳过 `set_next_task_fair()`，于是没有任何东西为下一个 fair 抢占点重新武装 hrtick。结果：fair 任务的调度粒度/抢占时点就静默丢失了，直到有别的契机（比如 tick 或 enqueue/dequeue）才重新触发。这是一个抢占会计上的正确性缺口，不是崩溃/死锁。

## 技术方案

引入新的 `next == prev` 回调语义 `SNT_REPICK`：`put_prev_set_next_task(rq, prev, next)` 在 `next == prev` 时调用 `next->sched_class->set_next_task(rq, next, SNT_REPICK)`；`set_next_task_fair()` 对 `SNT_REPICK` 跳过任务切换相关的工作，只重启 fair hrtick。`hrtick_start()` 在 `schedule()` 期间记录延迟，`hrtick_schedule_exit()` 重新武装定时器。对 SCHED_DEADLINE 不在 `SNT_REPICK` 时重启 dl hrtick——same-task repick 对 fair 和 SCHED_DEADLINE 都会跳过 `put_prev_task()`，但 DL 侧无需重启。合入版本 diffstat：kernel/sched 下 fair/core/deadline 共约 8 处改动。

## 版本演进与当前进展

- v1（2026-08-13，msgid `<20260813-sched-fair-hrtick-restart-v1-1-4230d1e18fbb@gentwo.org>`）：重启 fair hrtick 的首版。
- v2（2026-09-11，`<20260911-sched-fair-hrtick-restart-v2-1-0d34db26ecd1@gentwo.org>`）：用 SNT_REPICK 取代 fair 专用状态，fair/DL 都重启。
- v3（2026-09-15，`<20260915-sched-fair-hrtick-restart-v3-1-7517f388f0c8@gentwo.org>`）：移除 SCHED_DEADLINE 的 SNT_REPICK 重启；获 Zhan Xusheng Reviewed-by。
- v4（2026-09-17，`<20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org>`）：澄清 fair/DL 重启差异、文档化 SNT_* 调用点语义。
- 09-25：Peter 以 v4 合入 tip/sched/core（Commit-ID c72945693b90423f1b46ac2dbc8749c2b7804fc8）。

## Maintainer 意见与讨论焦点

K Prateek Nayak 早期参与了语义澄清：`SNT_REPICK` 应当「在 hrtick 到期后重启 fair hrtick」，但 DL 是否也该重启存在分歧，v3 起明确 DL 不做 SNT_REPICK 重启，即同日被 v14 proxy-exec 系列（<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-011-sched-make-proxy-execution-compatible-with-sched-ext.html">sched-20260925-011</a>）引用的那个 SNT_CONFIRM/SNT_REPICK 机制的前身。Peter Zijlstra 作为 committer 直接收取 v4，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit c72945693b90423f1b46ac2dbc8749c2b7804fc8，随 sched/core 分支进入下一合并窗口。*blocking_issues* 无。

## 效果评估

合入邮件未附 benchmark 或复现数据；这是一个抢占点会计的确定性正确性修复，效果静态可证（repick 后 hrtick 不再失活）。暂无效果数据。

## 我可以参与的点

修复已合入，当前阶段无明显参与空间。若自家分支使用 hrtick（CONFIG_SCHED_HRTICK），回合时需连同 `SNT_REPICK` 回调语义一并带回，注意其与 v14 proxy-exec 系列使用的 `SNT_CONFIRM` 是相邻改动（*review*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033365349.2819794.3113821108284833728.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/c72945693b90423f1b46ac2dbc8749c2b7804fc8
- v4 补丁: https://lore.kernel.org/all/20260917-sched-fair-hrtick-restart-v4-1-4dd1414da81a@gentwo.org/
