---
id: sched-20261022-007
date: 2026-10-22
subject: 'sched/eevdf: Move to a single runqueue'
subsystem: sched
type: discussion
status: under_review
severity: medium
thread_root_msgid: null
lore_url: https://lore.kernel.org/all/40443762033546b89044587f40b21018971a9867.camel@gmx.de/
authors:
- Peter Zijlstra
maintainers_involved:
- Vincent Guittot
current_version: v3
patch_series: []
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 继续观察 cpu.idle 抢占修复与 nice 19 使用建议的落地反馈
contribution_opportunities:
- kind: testing
  description: 复现 Mike 的 cpu.idle hog-vs-wakelat 实验，厘清预期语义
- kind: discussion
  description: 就 nice 19 尾延迟需不需要补丁级修复参与讨论
generated_at: '2026-10-23T01:20:00'
source_email_count: 2
related_articles:
- sched-20261021-014
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
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-014-sched-eevdf-move-to-a-single-runqueue.html">sched-20261021-014</a>：Vincent 给出 rt-app 量化数据解释 nice 19/short-task 回退——7.2.9 相比 7.3，短周期任务 outlier 数 17→632、平均唤醒延迟 54µs→145µs、99.9th 1582µs→2132µs；并为短任务设置 slice=1ms 后两者都回归正常。结论：flat 层级改变了权重计算，正 vlag 消逝更快、slice protection 更活跃。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-007-sched-eevdf-move-to-a-single-runqueue.html">sched-20261022-007</a>（今天）：Jakub 表示会先改自己的负载（从 KDE kwin 的 MR 开始），并希望 cpu.idle 与 nice 19 问题都能解决、否则「太具破坏性」。Mike Galbraith 贴出 perf sched 数据自问「是否测错了」——其数据中 `cpu.idle=1` 让 wakelat 的 >1ms 唤醒从 4568 降到 0，与他的叙述存在张力，并提示存在 DELAY_DEQUEUE 抖动。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> → <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261020-003</a>）单运行队列落地 v7.3 后，社区追查短任务/`cpu.idle` 场景的尾延迟回退。此前已分流出两条线索：`cpu.idle` 抢占（已独立成篇 001 修复）与「nice 19 / short-task 延迟」。今日无新根因补充，进展集中在「受影响方如何应对」与「cpu.idle 行为是否如预期」的实测讨论。

## 技术方案
（今日无新补丁，为使用建议与实测数据）Vincent 此前给出的结论仍是主线：flat 层级改变了计算 vruntime、deadline、vlag 所用的 weight，使正 vlag 消逝更快、slice protection 更活跃；对需要优先运行的短任务，正确做法是显式 `sched_setattr(..., slice=1ms)`。今日 Jakub 从使用者侧确认会按此调整自身负载（kwin）；Mike 则用 cgroupA（cpu hog，cpu.idle 切换）+ cgroupB（wakelat）的 pinned 实验观察 cpu.idle 是否真的让 hog 让路。

## 版本演进与当前进展
*current_version: v3*（thread root 未获取到）。当日无新版本，为回归讨论的延续。

## Maintainer 意见与讨论焦点
今日回帖者非补丁作者：Jakub Okoński（KDE/kwin）表示接受现状并自行适配负载，但强调「希望 cpu.idle 与 nice 19 都解决，否则太 disruptive」。Mike Galbraith 的实验数据里 `cpu.idle=1` 使 wakelat 的 >1ms 唤醒计数 4568→0（最大 2.4ms→0），但他自述「看到 wakelat 直接穿过 hog，与 cpu.idle 状态无关」，并自问「是否测错了」；他还提示同一实验里存在 DELAY_DEQUEUE 导致的抖动（cpu.idle=0 时 wakelat runtime delta 的差异他归因于此）。

## 合入评估
*likelihood=unknown*。单运行队列本身已合入 v7.3，本线程是合入后回归的后续讨论，不涉及新的合入决策；*blocking_issues*：cpu.idle 抢占语义（见 005 篇）与 nice 19/short-task 尾延迟仍在收敛中；*next_action*：继续观察 cpu.idle 修复（001/005 线）与 nice 19 使用建议的落地反馈。

## 效果评估
Mike Galbraith 今日贴出 perf sched 数据：`cpu.idle=1` 时 wakelat >1ms 唤醒 0 次（vs cpu.idle=0 时 4568 次），但其测试方法与结论自认为存疑（他提示忽略 perf 的 max 值、以 awk 处理的 wakelat 输出为准，并指出 DELAY_DEQUEUE 是抖动来源）。

## 我可以参与的点
- *kind: testing*：复现 Mike 的 cpu.idle hog-vs-wakelat 实验，厘清「cpu.idle 是否应让 hog 让路」的预期语义。
- *kind: discussion*：就 nice 19 短任务尾延迟是否需要补丁级修复、还是显式 slice 设置即为答案，参与讨论。

## 参考链接
- 线程入口（上日 Vincent 回帖）：https://lore.kernel.org/all/CAKfTPtBVJZ7DUeDci=JkCs1kstoYXsBru46VchZV7DE5=RB2+w@mail.gmail.com/
- Mike 今日回帖：https://lore.kernel.org/all/40443762033546b89044587f40b21018971a9867.camel@gmx.de/
- Jakub 今日回帖：https://lore.kernel.org/all/a82eb30e-685a-4ee3-af49-36b1102587de@okonski.org/
