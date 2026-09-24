---
id: sched-20260917-009
date: '2026-09-17'
subject: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
subsystem: sched
type: fix
status: under_review
severity: medium
thread_root_msgid: <20260917075242.2813147-1-fangqiurong@kylinos.cn>
lore_url: https://lore.kernel.org/all/20260917075242.2813147-1-fangqiurong@kylinos.cn/
authors:
- Qiurong Fang
maintainers_involved:
- Tejun Heo
- Andrea Righi
current_version: v4
patch_series:
- version: v3
  msgid: <20260916070753.3343113-1-fangqiurong@kylinos.cn>
  date: '2026-09-16'
  summary: consume/move 路径解锁 DSQ 后再调用 ops.dequeue()
  review_outcome: Tejun 给出文案与清理意见
- version: v4
  msgid: <20260917075242.2813147-1-fangqiurong@kylinos.cn>
  date: '2026-09-17'
  summary: 按 Tejun 意见收尾：注释措辞、删 @src_dsq 参数、selftest 从 run() 轮询
  review_outcome: 评审收敛，等待合入
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 等待 Tejun 应用到 sched_ext 分支
contribution_opportunities:
- kind: testing
  description: 用 ops.dequeue() 内锁源 DSQ 的 BPF 调度器跑 dequeue_iter selftest
- kind: review
  description: 核对 selftest 改从 run() 轮询后仍覆盖 consume/move 两路径
generated_at: '2026-09-18T09:00:00'
source_email_count: 5
related_articles:
- sched-20260916-006
tags:
- sched_ext
title: 'sched_ext: Don''t run ops.dequeue() with a DSQ lock held'
layout: article
---

## TL;DR
增量更新：Qiurong Fang 推出 v4，落实 Tejun Heo 对 v3 的全部评审意见（终端分支注释措辞、删除未用的 @src_dsq 参数、修正 commit message 用词、selftest 从 run() 直接轮询）。该修复解决 consume/move 路径持源 DSQ 锁调用 ops.dequeue() 的自死锁问题，已 Cc: stable v7.1+，patch 1 带 Andrea Righi 的 Acked-by，合入可能性高。

## 背景与问题
背景见 <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-006-sched-ext-dont-run-ops-dequeue-with-a-dsq-lock-held.html">sched-20260916-006</a>：consume 与 move 路径在持有源 user DSQ 锁时调用 ops.dequeue()，任何从 ops.dequeue() 内再锁同一 DSQ 的 BPF 调度器都会自死锁。方案是把调用移到 DSQ 解锁之后。

## 技术方案
方案不变。关键语义澄清（据 Tejun 评审）：回调在 @dsq->lock 释放后运行，但 rq lock 在每条路径上都仍被持有，因此注释不能写"unlocked"，要写"after @dsq->lock is dropped"。

## 版本演进与当前进展
- v3（09-16，`<20260916070753.3343113-1-fangqiurong@kylinos.cn>`）：上一版。
- v4（09-17，`<20260917075242.2813147-1-fangqiurong@kylinos.cn>`）：按 Tejun 意见收尾——终端分支注释措辞、删除 `scx_move_local_task_to_local_dsq()` 未用参数 @src_dsq（含 sub.c 三处调用）、commit message 去"there"、selftest 头部注释重写并改从 run() 直接轮询。

## Maintainer 意见与讨论焦点
- **Tejun Heo（v3 评审）**：逐条给出文案与代码意见（"there 没有指代"、"回调并非 unlocked，rq lock 每条路径都在"、"@src_dsq 未用请删除并同步三处调用"），v4 全部落实。
- **Andrea Righi**：v1 阶段已给出 Acked-by（patch 1）。
- 无分歧；处于合入前的最终收尾。

## 合入评估
*likelihood=high*。带 Cc: stable 的自死锁修复，评审已收敛到纯文案/清理层面，Tejun 无实质异议。*blocking_issues*：无实质阻塞。*next_action*：等待 Tejun 应用到 sched_ext/for-7.3-fixes 或相应分支。

## 效果评估
无性能数据；属正确性（死锁）修复。

## 我可以参与的点
- kind=testing：用带 ops.dequeue() 内锁源 DSQ 的 BPF 调度器跑 selftest `dequeue_iter`，验证不再自死锁。
- kind=review：核对 v4 selftest 从 run() 直接轮询后是否仍覆盖 consume 与 move 两条路径。

## 参考链接
- lore（v4 cover）: https://lore.kernel.org/all/20260917075242.2813147-1-fangqiurong@kylinos.cn/
