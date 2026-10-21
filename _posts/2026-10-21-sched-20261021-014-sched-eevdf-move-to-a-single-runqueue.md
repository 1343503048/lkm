---
id: sched-20261021-014
date: 2026-10-21
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/CAKfTPtBVJZ7DUeDci=JkCs1kstoYXsBru46VchZV7DE5=RB2+w@mail.gmail.com/
authors:
- Vincent Guittot
maintainers_involved:
- Vincent Guittot
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: high
  blocking_issues: []
  next_action: 观察社区对短任务默认 slice 语义的后续共识
contribution_opportunities:
- kind: discussion
  description: 参与短任务默认 slice 语义是否需要调整的讨论
generated_at: '2026-10-22T01:30:00'
source_email_count: 1
related_articles:
- sched-20261020-003
tags:
- eevdf
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见下。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> / 20261007-009：Aishwarya Rambhadran 报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 配置 p99 回退 ~30%，bisect 指向「Move to a single runqueue」；后续怀疑点收敛到 WA_WEIGHT/task_h_load。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-002-sched-eevdf-move-to-a-single-runqueue.html">sched-20261016-002</a>：Jakub Okoński 给出可复现量化回归——单运行队列疑似破坏 `cpu.idle` cgroup 的 wakeup preemption（wakelat p99 12µs→2029µs）。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261020-003</a>：Vincent 把 `cpu.idle` 抢占修复内联发出（后独立成篇为 001），Jakub 确认修好 cpu.idle 但 nice 19 仍回退。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-014-sched-eevdf-move-to-a-single-runqueue.html">sched-20261021-014</a>（今天）：Vincent 给出 rt-app 量化数据解释 nice 19/short-task 回退——7.2.9 相比 7.3，短周期任务 outlier 数 17→632、平均唤醒延迟 54µs→145µs、99.9th 1582µs→2132µs；并为短任务设置 slice=1ms 后两者都回归正常。结论：flat 层级改变了 vruntime/deadline/vlag 的权重计算，正 vlag 让 slice protection 更活跃，短任务应显式设 slice 来请求优先运行。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> → <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261020-003</a>）单运行队列落地 v7.3 后，社区追查短任务/`cpu.idle` 场景的尾延迟回退。此前已分流出两条线索：`cpu.idle` 抢占（已独立成篇 001 修复）与「nice 19 / short-task 延迟」。今日 Vincent 聚焦后者，用 rt-app 短周期唤醒任务给出量化对比，并解释根因——flat 层级下权重计算方式改变，导致正 vlag 的消逝方式不同、slice protection 更活跃。

## 技术方案
（今日为根因解释与使用建议，非新补丁）Vincent 说明：flat 层级改变了计算 vruntime、deadline、vlag 所用的 weight，使正 vlag 消逝更快、slice protection 更活跃；这是「让 lag 更快消逝、任务不应在睡眠时永久保留 lag」的既定趋势。对需要优先运行的短任务，正确做法是显式 `sched_setattr(..., slice=1ms)`，而非依赖默认公平语义。

## 版本演进与当前进展
*current_version: 主线 v7.3*（无新版本，今日为回归根因量化与解释）。

## Maintainer 意见与讨论焦点
Vincent Guittot（作者/sched 维护者）给出数据与定性结论：7.2.9→7.3 的短任务延迟劣化来自 flat 层级的权重/vlag 语义变化，属预期趋势；应用通过设置 slice 来表达「优先运行」意图，fairness 不破即可。无其他维护者今日回帖。

## 合入评估
*likelihood=high（语义维持）*。这不是「待合入补丁」而是已落地特性的回归澄清；Vincent 的结论是行为符合设计意图。*blocking_issues*：无新阻塞，但 nice 19 / 短任务的体验回退是否需进一步缓解仍待社区共识。*next_action*：观察是否有针对「短任务默认 slice」的后续调整或文档澄清。

## 效果评估
Vincent 的 rt-app 数据（短任务周期性唤醒）：
- v7.2.9：outlier 17、平均 54µs、99th 53µs、99.9th 1582µs、max 2248µs。
- v7.3：outlier 632、平均 145µs、99th 2039µs、99.9th 2132µs、max 3367µs。
- 给短任务设 slice=1ms 后，v7.3 的 outlier 11、平均 52µs、99.9th 55µs、max 57µs，与 7.2.9 持平。数据明确支撑「显式 slice 可恢复」。

## 我可以参与的点
- `discussion`：短任务默认行为是否需要在文档/默认值层面调整（例如对期望优先运行的任务是否应自动感知），可参与社区对该语义取舍的讨论。

## 参考链接
- Vincent 的 rt-app 数据：https://lore.kernel.org/all/CAKfTPtBVJZ7DUeDci=JkCs1kstoYXsBru46VchZV7DE5=RB2+w@mail.gmail.com/
