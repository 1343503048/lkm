---
id: sched-20260918-020
date: '2026-09-18'
subject: 'sched/core: Avoid false migration warning for proxy donors'
subsystem: sched
type: fix
status: merged_tip
severity: low
thread_root_msgid: <20260915184101.2621252-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20260915184101.2621252-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Peter Zijlstra
- John Stultz
current_version: v1
patch_series:
- version: v1
  msgid: <20260915184101.2621252-1-arighi@nvidia.com>
  date: '2026-09-15'
  summary: set_task_cpu 告警排除被阻塞 proxy donor
  review_outcome: John Stultz Acked-by；Peter 合入 tip/sched/urgent
upstream_commit: fe3c73d7bc769e7afc252f867a3421fe168b898d
fixes_commit: b049b81bdff6
merged_branch: tip/sched/urgent
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 跟踪随 sched/urgent 进入主线
contribution_opportunities: []
generated_at: '2026-09-19T09:00:00'
source_email_count: 1
related_articles:
- sched-20260916-001
tags:
- proxy_execution
- migration
title: 'sched/core: Avoid false migration warning for proxy donors'
layout: article
---

## TL;DR
增量更新：Andrea Righi 的 proxy execution 修复（避免对 migration-disabled 的被阻塞 donor 误报迁移告警）本日被 Peter Zijlstra 合入 tip 的 `sched/urgent` 分支（commit fe3c73d7bc76），Fixes b049b81bdff6，已获 John Stultz Acked-by。将随 sched/urgent 进入主线。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-001-sched-core-avoid-false-migration-warning-for-proxy-donors.html">sched-20260916-001</a>：proxy execution 会把被阻塞 donor 的调度上下文搬到锁 owner 的 CPU，即使该 donor 处于 migration-disabled 状态；donor 并不在那里执行，其原始执行 CPU 仍记录在 `wake_cpu`。`set_task_cpu()` 对 migration-disabled 任务无条件告警，于是随后的 proxy 迁移或唤醒返回路径触发误报——搬动被阻塞的调度上下文并不违反 migration-disabled 的执行上下文约束。

## 技术方案
在 `set_task_cpu()` 的告警中排除被阻塞的 proxy donor（`sched_proxy_exec() && p->is_blocked && task_cpu(p) != p->wake_cpu`），proxy 唤醒路径在清除 blocked 状态前会先恢复可执行放置。`kernel/sched/core.c` 8 增 1 删。

## 版本演进与当前进展
- v1（09-15，`<20260915184101.2621252-1-arighi@nvidia.com>`）：本日合入 `tip/sched/urgent`。

## Maintainer 意见与讨论焦点
- **Peter Zijlstra**：作为 committer 合入 `sched/urgent`，无异议。
- **John Stultz**：Acked-by。

## 合入评估
*likelihood=merged*。已合入 tip `sched/urgent` 分支（Commit-ID fe3c73d7bc769e7afc252f867a3421fe168b898d）。*blocking_issues*：无。*next_action*：跟踪该 commit 随 sched/urgent 进入主线。

## 效果评估
作者给出复现场景（CPU1 建 mutex owner、CPU0 建 migration-disabled waiter）会触发 `WARNING: kernel/sched/core.c:3389 at set_task_cpu`；修复后该路径不再误报。无性能数据。

## 我可以参与的点
当前阶段暂无明显参与空间（已合入），可持续观察 proxy execution 相关后续修复。

## 参考链接
- tip gitweb: https://git.kernel.org/tip/fe3c73d7bc769e7afc252f867a3421fe168b898d
- lore（patch）: https://lore.kernel.org/all/20260915184101.2621252-1-arighi@nvidia.com/
