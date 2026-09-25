---
id: sched-20260925-006
date: 2026-09-25
subject: 'sched/fair: Randomize equally shallow slow-path candidates'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <179033364754.2819794.12206803922125590104.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033364754.2819794.12206803922125590104.tip-bot2@tip-bot2/
upstream_commit: c9ce69fc43bd07dbed9d23a504e56f84604ecf42
fixes_commit: null
merged_branch: tip/sched/core
current_version: v2
generated_at: '2026-09-26T01:15:00'
authors:
- Christian Loehle
maintainers_involved:
- Peter Zijlstra
- Vincent Guittot
patch_series:
- version: v1
  msgid: <20260916100116.701206-1-christian.loehle@arm.com>
  date: 2026-09-16
  summary: 删除 idle-recency tie-break + reservoir sampling
  review_outcome: Kayra/Sashiko 关切小核数与随机性
- version: v2
  msgid: <20260917153915.1563875-3-christian.loehle@arm.com>
  date: 2026-09-17
  summary: 拆 1/2（drop idle recency）+ 2/2（本枚，U64_MAX reservoir）
  review_outcome: Vincent Guittot Reviewed-by；09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities:
- kind: testing
  description: 并发唤醒压力场景（大量短任务同时 slow-path）下随机化打破扫描顺序偏差的收益量化仍缺数据
source_email_count: 1
related_articles:
- sched-20260918-004
- sched-20260917-007
tags:
- cfs
- idle
- load_balance
title: 'sched/fair: Randomize equally shallow slow-path candidates'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-004-sched-fair-randomize-equally-shallow-slow-path-candidates.html">sched-20260918-004</a> / <a class="article-ref" href="/lkm/2026/09/17/sched-20260917-007-sched-fair-randomize-equally-shallow-slow-path-candidates.html">sched-20260917-007</a>。Christian Loehle 的「用 reservoir sampling 随机化同等 exit latency 的 slow-path 候选」补丁（v2 系列 2/2）已被 Peter Zijlstra 合入 tip/sched/core（commit c9ce69fc43bd07dbed9d23a504e56f84604ecf42，09-25 12:45:58 +0200），与 1/2（<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-005-sched-fair-drop-idle-recency-from-slow-path-cpu-selection.html">sched-20260925-005</a>）同批合入。

## 背景与问题

slow-path 选择器总是选第一个合格的 idle CPU，会留下扫描顺序偏差（scan-order bias）：并发的多个 slow-path 选择器可能在任何一个任务入队之前都选中同一个 CPU，导致碰撞。需要对同等 exit 延迟的候选做随机化，打破这种偏差。

## 技术方案

对相同 exit 延迟使用 reservoir sampling（蓄水池采样），出现更浅候选时重置候选计数；用 per-CPU scheduler PRNG + `reciprocal_scale()` 避免可变除法或第二次扫描。用 u64 latency key，未发布状态用 U64_MAX；已发布状态优先，没有已发布状态时在无发布状态的 idle CPU 中采样。合入版本 diffstat：kernel/sched/fair.c 共 12 insertions(+), 6 deletions(-)。

## 版本演进与当前进展

- v1（2026-09-16，`<20260916100116.701206-1-christian.loehle@arm.com>`）：删除 idle-recency tie-break + reservoir sampling。
- v2（2026-09-17，`<20260917153915.1563875-1-christian.loehle@arm.com>`）：拆 1/2 + 2/2；本枚为 2/2，msgid `<20260917153915.1563875-3-christian.loehle@arm.com>`。
- 09-25：Peter 合入 tip/sched/core（Commit-ID c9ce69fc43bd07dbed9d23a504e56f84604ecf42），带 Vincent Guittot Reviewed-by。

## Maintainer 意见与讨论焦点

Vincent Guittot 对本枚给出 Reviewed-by。v1 阶段 Kayra/Sashiko 曾对小核数场景的随机性与行为提出关切，v2 拆分后以「U64_MAX 表示未发布状态、已发布状态优先」收敛。Peter Zijlstra 作为 committer 收取，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit c9ce69fc43bd07dbed9d23a504e56f84604ecf42。*blocking_issues* 无。

## 效果评估

与 1/2 一同由 Doug Smythies 实测（详见 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-005-sched-fair-drop-idle-recency-from-slow-path-cpu-selection.html">sched-20260925-005</a>）：9 forks +1.47%、25 档 forks 多档 +0.3~5.7%、3600s dwell +2.44%、并发随机 HDD 读 patched 更好，总体 +1~3%。随机化本身对单机数值影响是二阶的（打破扫描顺序偏差，主要影响并发 slow-path 的碰撞），作者未单独给本枚数据。

## 我可以参与的点

修复已合入，无代码参与空间；并发唤醒压力场景（大量短任务同时 slow-path）下随机化收益的量化仍缺数据（*testing*）。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364754.2819794.12206803922125590104.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/c9ce69fc43bd07dbed9d23a504e56f84604ecf42
- v2 2/2 补丁: https://lore.kernel.org/all/20260917153915.1563875-3-christian.loehle@arm.com/
