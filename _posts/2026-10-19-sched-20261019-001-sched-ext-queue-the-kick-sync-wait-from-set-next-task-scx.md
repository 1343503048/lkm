---
id: sched-20261019-001
subject: 'sched_ext: Queue the kick_sync wait from set_next_task_scx()'
date: 2026-10-19
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20261018162415.55913-1-arighi@nvidia.com>
lore_url: https://lore.kernel.org/all/20261018162415.55913-1-arighi@nvidia.com/
authors:
- Andrea Righi
maintainers_involved:
- Tejun Heo
current_version: v2
patch_series:
- version: v1
  msgid: <20261017202025.3834954-1-arighi@nvidia.com>
  date: 2026-10-18
  summary: core-sched 掉锁修复（1/2，已应用 for-7.3-fixes）+ kick_sync wait 在 dispatch 前取下/必要时再排队（2/2）
  review_outcome: 1/2 应用；2/2 Tejun 建议改用 set_next_task_scx() 排队并放 for-7.4
- version: v2
  msgid: <20261018162415.55913-1-arighi@nvidia.com>
  date: 2026-10-19
  summary: 从 set_next_task_scx() 的 SNT_PICK/SNT_REPICK 排队 kick_sync wait；kick_sync_pending
    在 callback 运行时清除
  review_outcome: 暂无回帖
upstream_commit: null
fixes_commit: 415cb193bb97
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues:
  - 暂无今日回帖，待 Tejun 最终收取
  next_action: 等 sched_ext 维护者 review 并应用到 for-7.4
contribution_opportunities:
- kind: testing
  description: SMT+SCHED_CORE 压测 kick_sync wait 路径，验证 rq_pin_lock() WARNING 不再触发
- kind: review
  description: 复核 set_next_task_scx() SNT_PICK/SNT_REPICK 排队与 proxy exec 下 kick_sync_pending
    清除时机的交互
generated_at: '2026-10-20T01:30:00'
source_email_count: 1
related_articles:
- sched-20261010-009
- sched-20261015-020
- sched-20261017-002
- sched-20261018-006
tags:
- sched_ext
- core_sched
title: 'sched_ext: Queue the kick_sync wait from set_next_task_scx()'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/10/18/sched-20261018-006-sched-ext-fix-scx-balance-callbacks-queued-across-a-core-sch.html">sched-20261018-006</a>：Andrea Righi 发 `Fix scx balance callbacks queued across a core-sched pick`（2 补丁）修复 ff0545e0c263 遗留的 core-sched 缺口；1/2 已被 Tejun 应用到 `sched_ext/for-7.3-fixes`；2/2（kick_sync wait）Tejun 建议改到 for-7.4 按「从 set_next_task_scx() 排队」的新思路做。
- <a class="article-ref" href="/lkm/2026/10/19/sched-20261019-001-sched-ext-queue-the-kick-sync-wait-from-set-next-task-scx.html">sched-20261019-001</a>（今天）：Andrea 发 v2 单补丁落实 Tejun 建议——把 kick_sync wait 移到 `set_next_task_scx()` 的 SNT_PICK/SNT_REPICK 排队，并因 proxy exec 会 zap balance callback 改为在 callback 运行时清 `kick_sync_pending`。带 `Fixes: 415cb193bb97`、`Cc: stable v7.0+`。

## 背景与问题

（承接 20261018-006）SCX_KICK_WAIT wait 被推迟到 `rq->scx.kick_sync_bal_cb`，由最后一次 pick 在本地 rq 上排队。但 core scheduling 下「返回任务的 pick」并非终态：`pick_next_task()` 会继续挑 SMT sibling，sibling 的 dispatch 可能在 callback 仍排队时释放共享 rq 锁——此窗口内取得 rq 锁的 CPU 发现 pending balance callback，触发 `rq_pin_lock()` 的 WARNING。前作 ff0545e0c263 只在 pick 最终确定时才排队 callback，但 kick_sync wait 属于「必须等到 SCX 任务真正开跑」的等待，不能像普通 deferred work 那样直接 punt 到 irq_work，需专门处理。

## 技术方案

单补丁（`kernel/sched/ext/`），v2 落实 Tejun 两点意见：

- 从 `set_next_task_scx()` 的 **SNT_PICK 与 SNT_REPICK** 排队 kick_sync wait。`put_prev_set_next_task()` 在 pick 最终确定、core-wide 选择完成之后才调用 `set_next_task_scx()`，因此 rq 锁不可能带着已排队的 callback 被释放。若 CPU 最终跑 idle 或更高类任务，则其上没有 SCX 任务可等，`kick_sync_pending` 保持置位、下次 SCX pick 再等待。
- `kick_sync_pending` 改为在 callback **运行时**清除（而非排队时），因为 for-7.4 的 proxy exec 会 zap balance callback、`find_proxy_task()` 失败后再 pick，排队时清除会丢失状态。

## 版本演进与当前进展

*current_version: v2*。

- v1（20261018-006 的 2/2，msgid `<20261017202025.3834954-1-arighi@nvidia.com>`）：每次 core-wide 选择期间 dispatch 前把 wait 从本地 rq 取下、必要时再排队。
- v2（今天，`<20261018162415.55913-1-arighi@nvidia.com>`）：按 Tejun 建议改到 `set_next_task_scx()` 排队，`kick_sync_pending` 在 callback 运行时清除。带 `Fixes: 415cb193bb97` 与 `Cc: stable v7.0+`（含 c72945693b90 依赖标签）。

## Maintainer 意见与讨论焦点

Tejun Heo（sched_ext 维护者）在前作（20261018-006）中给出本轮改版依据：不认同「每次 dispatch 前取下、必要时再排」的搬动，要求从 `set_next_task_scx()` 的 SNT_PICK/SNT_REPICK 排队（`put_prev_set_next_task()` 在 pick 最终确定后才调它）；并指出 proxy exec 会 zap balance callback，`kick_sync_pending` 应在 callback 运行时而非排队时清除。v2 逐条落实，今天暂无新增回帖。

## 合入评估

*likelihood=high*。1/2（core-sched 掉锁核心缺口）已进 `sched_ext/for-7.3-fixes`；本 v2 方向与实施位置均由 Tejun 指定、带稳定依赖标签，符合 for-7.4 走向。*blocking_issues*：等待 Tejun 对 v2 的最终收取（暂无今日回帖）。*next_action*：等 sched_ext 维护者 review 并应用到 for-7.4。

## 效果评估

无量化性能数据，属正确性修复。作者在 20261018-006 中给出复现：仅 ff0545e0c263 时 debug 检查 10 次中 5 次触发、伴随 WARNING，加 1/2 后 16 次 0 触发；kick_sync 场景用同一 setup + 临时改 scx_qmap 复现。v2 单补丁未附新增测试数据。

## 我可以参与的点

- `testing`：在 SMT + SCHED_CORE 机器上压测 kick_sync wait 路径（`SCX_KICK_WAIT` 踢另一 core 的 CPU），验证 v2 后 `rq_pin_lock()` WARNING 不再触发。
- `review`：复核 `set_next_task_scx()` SNT_PICK/SNT_REPICK 排队与 proxy exec 下 `kick_sync_pending` 清除时机的交互。

## 参考链接

- v2 patch：https://lore.kernel.org/all/20261018162415.55913-1-arighi@nvidia.com/
- v1 链接（作者自附）：https://lore.kernel.org/r/20261017202025.3834954-3-arighi@nvidia.com/
