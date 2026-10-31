---
id: sched-20261031-015
date: 2026-10-31
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/40443762033546b89044587f40b21018971a9867.camel@gmx.de/
authors:
- Peter Zijlstra
maintainers_involved: []
current_version: v3
patch_series: []
upstream_commit: 333238da9a19
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 维护者（Vincent/Peter）未回应 333238da9a19 的机理与数据
  - 「修正时间更新 vs 回退单运行队列整体」路线未定
  next_action: 等 Vincent/Peter 对 333238da9a19 数据的回应，决定 fix 还是 revert
contribution_opportunities:
- kind: review
  description: 分析 333238da9a19 与 DELAY_DEQUEUE event-driven now 更新的记账语义
- kind: testing
  description: 复跑 will-it-scale pipe-handoff 并配合 DELAY_DEQUEUE 开/关，量化该 commit 对 fastpath
    的占用
generated_at: '2026-11-01T09:00:00'
source_email_count: 1
related_articles:
- sched-20260923-001
- sched-20261007-009
- sched-20261016-002
- sched-20261020-003
- sched-20261021-014
- sched-20261022-007
- sched-20261030-003
tags:
- eevdf
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> / 20261007-009：Aishwarya Rambhadran 报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 配置 p99 回退 ~30%，bisect 指向「Move to a single runqueue」。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-002-sched-eevdf-move-to-a-single-runqueue.html">sched-20261016-002</a>：Jakub Okoński 给出可复现量化回归——单运行队列疑似破坏 `cpu.idle` cgroup 的 wakeup preemption（wakelat p99 12µs→2029µs）。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261020-003</a> / 20261021-014：Vincent 修好 `cpu.idle`，并用 rt-app 解释 nice 19/short-task 回退（flat 层级改变权重计算、正 vlag 消逝更快）。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-007-sched-eevdf-move-to-a-single-runqueue.html">sched-20261022-007</a>：Mike Galbraith 贴 perf sched 数据并提示存在 DELAY_DEQUEUE 抖动。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261030-003</a>：Chengfeng Lin 锁定 `333238da9a19`（"Update time before requeueing delayed entities"）——15 worker will-it-scale pipe-handoff 吞吐回退 15.69%、每 handoff 内核指令 +25%。
- <a class="article-ref" href="/lkm/2026/10/31/sched-20261031-015-sched-eevdf-move-to-a-single-runqueue.html">sched-20261031-015</a>（今天）：Mike Galbraith 进一步定位——DELAY_DEQUEUE 机制里那个 event-driven 的 "now" 更新在「消耗并占用」宝贵的 fastpath 周期，使 DELAY_DEQUEUE 可测量地变弱；`__dequeue_task()` 里的 `update_curr()` 也疑似冗余开销。

## 背景与问题
（承接）单运行队列落地 v7.3 后的短任务/`cpu.idle` 尾延迟回退，已逐步归因到交付后的 DELAY_DEQUEUE 相关 follow-up commit `333238da9a19`。今日 Mike Galbraith 从「why event-driven」的角度给出机理层面的补充：那些 "now" 更新本就是**事件驱动**设计的，`333238da9a19` 加的那一次在 DELAY_DEQUEUE 机器里消耗并占用了 fastpath 周期，把记账偏移到让 DELAY_DEQUEUE 可测量地变弱——20% util 探针下看起来「完全坏了」，但更细的测量显示它只是「sad」而非 dead。

## 技术方案
（今日为机理分析，非新补丁）Mike 的具体结论：

- DELAY_DEQUEUE 里的 "now" 更新「expends and banks precious fastpath cycles」，偏移了 bean counting，使 DELAY_DEQUEUE 变弱。
- `__dequeue_task()` 里那个 `update_curr()`（virgin flat 路径）也被认为是冗余开销——flat 变更下刚更新过 cfs_rq，层级更新就在下方，属于重复记账。

这为「修正或 revert `333238da9a19`」提供了第二个独立视角（与 Chengfeng 的吞吐/指令数数据互补）。

## 版本演进与当前进展
*current_version: v3（单运行队列系列；上版讨论 2026-10-30）*。今日无新补丁，进展是把「回退归因」进一步坐实在 DELAY_DEQUEUE 的时间更新上。

## Maintainer 意见与讨论焦点
- **Mike Galbraith（资深调度贡献者，非正式维护者）**：给出机理判断——DELAY_DEQUEUE 的 event-driven "now" 更新被 `333238da9a19` 拖累，`__dequeue_task()` 的 `update_curr()` 冗余。
- 当日无正式维护者（Vincent/Peter）回复；此前 nice 19 是否应靠显式 slice 的分歧仍无定论。

## 合入评估
*likelihood=medium*。今日的机理分析与 Chengfeng 的量化数据形成互补，使「修正/回退 `333238da9a19`」更具体；但仍需维护者确认。*blocking_issues*：维护者未回应；「修正时间更新 vs 回退单运行队列整体」路线未定。*next_action*：等 Vincent/Peter 对 `333238da9a19` 数据的回应，决定 fix 还是 revert。

## 效果评估
无新增数字；Mike 提供的是机理判断（「20% util 探针下看起来完全坏了，但更细测量显示只是 sad」），定性为主，未附数据。

## 我可以参与的点
- **review**：分析 `333238da9a19` 与 DELAY_DEQUEUE 的 event-driven "now" 更新的记账语义，判断是移除该更新还是修正其放置。
- **testing**：复跑 will-it-scale pipe-handoff 并配合 DELAY_DEQUEUE 开/关，量化该 commit 对 fastpath 周期的占用。

## 参考链接
- 单运行队列讨论主线: https://lore.kernel.org/all/40443762033546b89044587f40b21018971a9867.camel@gmx.de/
- Mike 今日分析: https://lore.kernel.org/all/5ab06e4740bb0fd177a96e0a31f933a27d081012.camel@gmx.de/
