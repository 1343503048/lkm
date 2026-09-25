---
id: sched-20260925-005
date: 2026-09-25
subject: 'sched/fair: Drop idle recency from slow-path CPU selection'
subsystem: sched
type: feature
status: merged_tip
severity: none
thread_root_msgid: <179033364901.2819794.2754506755194638696.tip-bot2@tip-bot2>
lore_url: https://lore.kernel.org/all/179033364901.2819794.2754506755194638696.tip-bot2@tip-bot2/
upstream_commit: abe440b3770fce8eb8ee92a563dfb55a7b9a1c0e
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
  summary: 去掉 idle-recency 偏好并用 reservoir sampling 随机化等 latency 候选（单枚）
  review_outcome: Kayra/Sashiko 关切与设计分歧待收敛
- version: v2
  msgid: <20260917153915.1563875-2-christian.loehle@arm.com>
  date: 2026-09-17
  summary: 拆分为 1/2（本枚，drop idle recency）+ 2/2（U64_MAX reservoir）
  review_outcome: Vincent Guittot Reviewed-by；09-25 Peter 合入 tip/sched/core
merge_assessment:
  likelihood: merged
  blocking_issues: []
  next_action: 已合入 tip/sched/core，等待进入合并窗口
contribution_opportunities:
- kind: testing
  description: Doug 的实测仅覆盖 x86 消费级 12 线程；arm64/大核服务器/NOHZ 场景下 slow-path 选择的影响仍缺数据，可补测回帖
source_email_count: 2
related_articles:
- sched-20260918-004
- sched-20260916-015
tags:
- load_balance
- idle
- cfs
title: 'sched/fair: Drop idle recency from slow-path CPU selection'
layout: article
---

## TL;DR

本文为增量更新，完整脉络见 related_articles 中的 <a class="article-ref" href="/lkm/2026/09/18/sched-20260918-004-sched-fair-randomize-equally-shallow-slow-path-candidates.html">sched-20260918-004</a> / <a class="article-ref" href="/lkm/2026/09/16/sched-20260916-015-sched-fair-randomize-equally-shallow-idle-cpu-picks.html">sched-20260916-015</a>。Christian Loehle 的「slow-path CPU 选择去掉 idle-recency 偏好」补丁（v2 系列 1/2）已被 Peter Zijlstra 合入 tip/sched/core（commit abe440b3770fce8eb8ee92a563dfb55a7b9a1c0e，09-25 12:45:58 +0200），与 2/2（<a class="article-ref" href="/lkm/2026/09/25/sched-20260925-006-sched-fair-randomize-equally-shallow-slow-path-candidates.html">sched-20260925-006</a>）同批合入；同日 Doug Smythies 贴出整组补丁的实测数据（总体 +1~3%）。

## 背景与问题

slow-path CPU 选择器偏好「最近 idle」的 CPU，把它当作 cache 热度的代理。但更新近的 idle stamp 可能意味着正在进入 idle：若该 CPU 无法中止 entry、必须完成 entry 再退出，代价可能比一个同等的已驻留 CPU 更高——而广告的最坏情况 exit 延迟已覆盖两种情形。idle_stamp 本身也不给当前 CPUIdle entry 打时间戳，所以这只是一个启发式。此外，近期 scheduler-idle 切换可能只是周期性任务活动的短暂间隙，说明该 CPU 可能很快又要忙起来。因此删除时间戳 tie-break、保留首个候选，除非找到更低的已发布 exit 延迟。

## 技术方案

删除 `idle_stamp` 时间戳 tie-break：除非找到更低的已发布 exit 延迟，否则保留首个候选。合入版本 diffstat：kernel/sched/fair.c 共 1 insertion, 15 deletions(-)。该枚与 2/2（用 reservoir sampling 随机化同等 exit latency 的候选）共同构成 v2 系列的机制。

## 版本演进与当前进展

- v1（2026-09-16，`<20260916100116.701206-1-christian.loehle@arm.com>`）：去掉 idle-recency 偏好 + reservoir sampling，单枚。
- v2（2026-09-17，`<20260917153915.1563875-1-christian.loehle@arm.com>`）：拆成 1/2（drop idle recency）+ 2/2（U64_MAX reservoir）；本枚为 1/2，msgid `<20260917153915.1563875-2-christian.loehle@arm.com>`。
- 09-25：Peter 合入 tip/sched/core（Commit-ID abe440b3770fce8eb8ee92a563dfb55a7b9a1c0e），带 Vincent Guittot Reviewed-by。

## Maintainer 意见与讨论焦点

Vincent Guittot 对本枚（及 2/2 见 <a class="article-ref" href="/lkm/2026/09/25/sched-20260925-006-sched-fair-randomize-equally-shallow-slow-path-candidates.html">sched-20260925-006</a>）给出 Reviewed-by，已随合入 commit 记录。历史分歧（v1 时 Kayra/Sashiko 对小核数与随机性的关切）在 v2 拆分后收敛。Peter Zijlstra 作为 committer 收取，本日无新分歧。

## 合入评估

已合入 tip/sched/core（*likelihood=merged*），commit abe440b3770fce8eb8ee92a563dfb55a7b9a1c0e。*blocking_issues* 无。

## 效果评估

Doug Smythies 在 Intel i5-10600K（6 核 12 CPU，kernel 7.3-rc3 baseline + 本 v2 系列）上做了四组测试，并注明可重复性较差、采用了 flush memory 与 15 分钟 dwell 稳态两种手段：

- 9 forks、60s×25 次：baseline 65867.05 → cl-rand 66832.20 bogos ops/sec，+1.47%。
- 1~25 forks 逐档（180s×各一次）：改善大多落在 0.3%~5.7%，25 档中仅 21 forks 一档 -0.61%，其余为负数为 0，整体正向。
- 9 forks、3600s dwell（取 17~56.67min 数据）：59740.52 → 61199.35，+2.44%。
- 500GB 文件并发随机 HDD 读：请求排队后 patched kernel 表现更好（见附件 actual.png）。

作者结论：该补丁集总体 +1~3% 改善。

## 我可以参与的点

修复已合入，无代码参与空间；Doug 的数据仅覆盖 x86 消费级 12 线程，arm64 / 大核服务器 / NOHZ 场景下 slow-path 选择的实际影响仍缺数据（*testing*），可补测并回帖。

## 参考链接

- lore thread（tip-bot 合入通知）: https://lore.kernel.org/all/179033364901.2819794.2754506755194638696.tip-bot2@tip-bot2/
- gitweb: https://git.kernel.org/tip/abe440b3770fce8eb8ee92a563dfb55a7b9a1c0e
- v2 1/2 补丁: https://lore.kernel.org/all/20260917153915.1563875-2-christian.loehle@arm.com/
- Doug Smythies 实测回帖: https://lore.kernel.org/all/008901dd4c81$4c95c9c0$e5c15d40$@telus.net/
