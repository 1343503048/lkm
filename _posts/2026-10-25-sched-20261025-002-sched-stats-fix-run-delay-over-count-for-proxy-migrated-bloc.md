---
id: sched-20261025-002
date: 2026-10-25
subject: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
subsystem: sched
type: fix
status: under_review
severity: low
thread_root_msgid: <20261025130740.3324391-1-albin_yang@163.com>
lore_url: https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/
authors:
- Wei Yang
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20261025130740.3324391-1-albin_yang@163.com>
  date: 2026-10-25
  summary: 新增 !task_is_blocked() 门控，任务仍阻塞在 mutex 上时不 re-arm last_queued
  review_outcome: 无当日 review
upstream_commit: null
fixes_commit: b049b81bdff6
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - Peter 对「delayed dequeue 与 proxy 分开修」口径的确认
  next_action: 与 v4 一并等 Peter 拍板
contribution_opportunities:
- kind: review
  description: 核对 task_is_blocked() 门控与 proxy 迁移路径的边界
- kind: testing
  description: 启用代理执行的构建上复现跨 CPU mutex 阻塞场景
generated_at: '2026-10-26T09:00:00'
source_email_count: 1
related_articles: []
tags:
- cfs
- sched_debug
- proxy_execution
title: 'sched/stats: Fix run_delay over-count for proxy-migrated blocked donors'
layout: article
---

## TL;DR
Wei Yang 在 run_delay v4（delayed dequeue 迁移多计修复）基础上补发独立单补丁，修 proxy execution 下被迁移的 blocked donor 的 run_delay 多计：mutex owner 在别的 CPU 上跑时，`find_proxy_task()` 把仍在阻塞的 donor 迁到 owner 的 CPU，迁移用 `activate_task(ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-arm 了 `last_queued`，导致阻塞时长被误算成等 CPU 时长。补丁新增 `!task_is_blocked()` 门控，2 CPU VM 实测同 ~170ms 阻塞从 ~167ms 降到 0.01ms。

## 背景与问题
proxy exec（v7.1 合入）下任务阻塞在内核 mutex 上（proxy donor），其 mutex owner 在另一 CPU 运行。`find_proxy_task()` 在「donor 被选为 next 但非 current、owner on_rq 且未 delayed」时，经 `proxy_migrate_task()` 把仍阻塞的 donor 迁到 owner 的 CPU。该迁移用 `attach_task()` → `activate_task(rq, p, ENQUEUE_NOCLOCK)`（不带 `ENQUEUE_RESTORE`）re-attach donor，于是 `sched_info_enqueue()` re-arm `last_queued`，尽管 donor 根本不 runnable——一次「假 enqueue」。真实唤醒不会纠正：donor 仍 on_rq 且非 `sched_delayed`，`ttwu_runnable()` 不调 `enqueue_task()`，`last_queued` 停留在迁移时刻；`sched_info_arrive()` 于是把迁移到真正运行之间的整个阻塞时长计为等 CPU 时间。这与 v4 修的「delayed dequeue 迁移多计」是**两个独立 bug**。`Fixes: b049b81bdff6`（"sched: Handle blocked-waiter migration (and return migration)"）。

## 技术方案
单补丁：任务仍阻塞在 mutex 上时不再 re-arm `last_queued`。delayed dequeue 睡眠者没有 `blocked_on`，所以这是对 `se.sched_delayed` 检查的**附加条件**而非替代（`!sched_delayed && !task_is_blocked()`），DELAY_DEQUEUE 修复不受影响。不能用 `!p->is_blocked` 门控：`ttwu_runnable()` 的真实唤醒 enqueue 在 `if (p->is_blocked)` 分支内、`is_blocked` 之后才在 `ttwu_do_wakeup()` 中清除，`!is_blocked` 会压掉本补丁依赖的 re-arm。

## 版本演进与当前进展
*current_version: v1*（`<20261025130740.3324391-1-albin_yang@163.com>`）。当日（10-25）新发，Applies on top of v4（`20261024042753.2276779-1-albin_yang@163.com`），作者明确标注「Kept separate」。

## Maintainer 意见与讨论焦点
无当日针对本补丁的维护者表态。作者在 v4 线程（见相关文章）回应了 Peter Zijlstra 关于为何不能用 `t->is_blocked` 门控的疑问，并论证：proxy migration 仅 v7.1 合入、delayed dequeue bug 自 v6.12 就存在，把二者耦合要么在 v6.12.y..v6.16.y 无法构建（无 proxy exec）、要么在 v6.17.y..v7.0.y 加上死依赖，故 proxy 侧单独发此补丁。

## 合入评估
*likelihood=high*。与 v4 同源的运行延迟修复，作者给出完整复现与数据，带明确 `Fixes:`；唯一待确认是 Peter 对「delayed dequeue 与 proxy 分开修」口径的最终拍板。*blocking_issues*：Peter 对拆分口径的确认。*next_action*：与 v4 一并等 Peter 拍板；作者已提供复现数据支撑拆分。

## 效果评估
2 CPU VM 实测（`run_delay` 为 `/proc/<tid>/schedstat` 第 2 字段，5 次迭代）：cross-cpu 未修时 169.9ms 阻塞计 167.1ms、加本补丁后 0.01ms；同 CPU 对照 167.3ms 阻塞 0.00ms。健全性检查：donor runnable 争 CPU 时，80ms 窗口内 `run_delay` 仍增 ~39ms（5/5），说明门控只压「假 enqueue」、不压真实等待。

## 我可以参与的点
- *kind: review*：核对 `task_is_blocked()` 门控与 proxy 迁移路径的边界（如 `blocked_on` 为 null 的情况）。
- *kind: testing*：在启用 SCHED_PROXY_EXECUTION 的构建上复现跨 CPU mutex 阻塞场景。

## 参考链接
- patch: https://lore.kernel.org/all/20261025130740.3324391-1-albin_yang@163.com/
- 前序 v4: https://lore.kernel.org/all/20261024042753.2276779-1-albin_yang@163.com/
