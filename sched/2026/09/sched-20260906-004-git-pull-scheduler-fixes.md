# [GIT PULL] scheduler fixes

## TL;DR

Ingo 向 Linus 发出 sched/urgent 修复拉取（顶端 `f0d243a96f26`），含 3 个调度修复：fair 类时间戳 bug、RT/DL push 候选跳过 migrate-disabled 任务、avg_idle 在无 idle_stamp 时跳过更新。属紧急修复，已基本合入主线。

## 背景与问题

这是 sched 子系统的周期性紧急修复汇总拉取，覆盖三个独立但都属于「正确性/稳健性」的修复点：
1. `pick_task_fair()` 与 `yield_task_fair()` 存在时间戳（timestamping）bug（Zhan Xusheng）。
2. RT 与 DL 调度器在挑选 push candidate 时未跳过 migrate-disabled 任务，可能推一个本不应被迁移的任务（Seiji Nishikawa）。
3. `rq->avg_idle` 在没有有效 `idle_stamp` 时仍被更新，产生无意义/错误的空闲时间统计（Shubhang Kaushik）。

## 技术方案

三处均为针对性小修复：时间戳修正、push 候选筛选增加 migrate-disabled 跳过、avg_idle 更新前校验 idle_stamp 有效性。属于已有稳定分支常见的小修小补，无架构性改动。

## 版本演进与当前进展

作为 sched/urgent 拉取请求（sched-urgent-2026-09-06）发出，顶端 commit 为 `f0d243a96f2684ad771d678767d17972cf840bd7`，由 Ingo 代 Peter 向 Linus 提交。通常此类 urgent 拉取会在合并窗口被直接合入。

## Maintainer 意见与讨论焦点

无公开分歧；urgent 分支修复经 tip 维护者内部认可后统一拉取。

## 合入评估

`merged_branch=tip/sched/urgent`、`likelihood=merged`。这是发给 Linus 的正式 pull request，按惯例会合入；无需社区额外动作。

## 效果评估

暂无独立 benchmark 数字；三处均为正确性修复（消除时间戳错误、避免错误 push、修正空闲统计），属稳健性提升。

## 我可以参与的点

当前阶段暂无明显参与空间，可持续观察后续 -stable 回合情况。

## 参考链接

- lore thread: 未获取到
- tip-bot commit: f0d243a96f2684ad771d678767d17972cf840bd7
- stable backport: 未获取到

---
id: sched-20260906-004
date: '2026-09-06'
subject: '[GIT PULL] scheduler fixes'
subsystem: sched
type: discussion
status: merged_tip
severity: none
thread_root_msgid: null
lore_url: null
upstream_commit: f0d243a96f2684ad771d678767d17972cf840bd7
fixes_commit: null
merged_branch: tip/sched/urgent
current_version: v1
generated_at: '2026-09-07T00:10:00'
authors:
- pr-tracker-bot@kernel.org
- Ingo Molnar
maintainers_involved:
- Peter Zijlstra
- Ingo Molnar
patch_series:
- version: v1
  msgid: null
  date: 2026-09-06
  summary: Ingo 向 Linus 发出 sched/urgent 拉取请求（sched-urgent-2026-09-06，顶端 commit f0d243a96f2684ad771d678767d17972cf840bd7），含 3 个调度修复：pick_task_fair()/yield_task_fair() 的时间戳 bug（Zhan Xusheng）；RT 与 DL 调度器挑
    push candidate 时跳过 migrate-disabled 任务（Seiji Nishikawa）；无有效 idle_stamp 时跳过 rq->avg_idle 更新（Shubhang Kaushik）。
  review_outcome: 作为 sched/urgent 修复拉取，方向已由 tip 维护者认可
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 等待 Linus 在合并窗口合入；无需社区额外动作
contribution_opportunities: []
source_email_count: 1
related_articles: []
tags:
- sched/fair
- rt
- deadline
- sched/core
---
