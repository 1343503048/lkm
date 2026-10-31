---
id: sched-20261030-003
date: 2026-10-30
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
upstream_commit: 333238da9a19
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - 需维护者 review 333238da9a19（Update time before requeueing delayed entities）的时间更新语义
  - 与 nice 19/short-task 既有回退的关系未理清
  next_action: 等维护者对 333238da9a19 回退数据的回应，决定 fix 还是 revert
contribution_opportunities:
- kind: testing
  description: 在 arm64/AMD 平台复跑 will-it-scale pipe-handoff，验证 333238da9a19 回退是否平台相关
- kind: review
  description: 分析 333238da9a19 对 DELAY_DEQUEUE 时间记账的影响，判断修正还是 revert
generated_at: '2026-10-31T09:00:00'
source_email_count: 2
related_articles:
- sched-20260923-001
- sched-20261007-009
- sched-20261016-002
- sched-20261020-003
- sched-20261021-014
- sched-20261022-007
tags:
- eevdf
- regression
title: 'sched/eevdf: Move to a single runqueue'
layout: article
---

## TL;DR
本文为增量更新，完整脉络见 related_articles。

- <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> / 20261007-009：Aishwarya Rambhadran 报告 v7.2→v7.3 在 AWS Graviton3 上个别 schbench 配置 p99 回退 ~30%，bisect 指向「Move to a single runqueue」；后续怀疑点收敛到 WA_WEIGHT/task_h_load。
- <a class="article-ref" href="/lkm/2026/10/16/sched-20261016-002-sched-eevdf-move-to-a-single-runqueue.html">sched-20261016-002</a>：Jakub Okoński 给出可复现量化回归——单运行队列疑似破坏 `cpu.idle` cgroup 的 wakeup preemption（wakelat p99 12µs→2029µs）。
- <a class="article-ref" href="/lkm/2026/10/20/sched-20261020-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261020-003</a>：Vincent 把 `cpu.idle` 抢占修复内联发出（后独立成篇为 001），Jakub 确认修好 cpu.idle 但 nice 19 仍回退。
- <a class="article-ref" href="/lkm/2026/10/21/sched-20261021-014-sched-eevdf-move-to-a-single-runqueue.html">sched-20261021-014</a>：Vincent 用 rt-app 量化解释 nice 19/short-task 回退，结论 flat 层级改变权重计算、正 vlag 消逝更快，短任务应显式设 slice=1ms。
- <a class="article-ref" href="/lkm/2026/10/22/sched-20261022-007-sched-eevdf-move-to-a-single-runqueue.html">sched-20261022-007</a>：Jakub 表示会先改自身负载，Mike Galbraith 贴 perf sched 数据自问是否测错，并提示存在 DELAY_DEQUEUE 抖动。
- <a class="article-ref" href="/lkm/2026/10/30/sched-20261030-003-sched-eevdf-move-to-a-single-runqueue.html">sched-20261030-003</a>（今天）：Chengfeng Lin 针对 Mike 在 wakeup-jitter 测试中指出的 commit `333238da9a19`（"sched: Update time before requeueing delayed entities"）补充 will-it-scale pipe-handoff 数据：15 worker 吞吐 v7.3 比 v7.1.3 低 15.69%（thread）/14.82%（process），单独 revert 该 commit 在 v7.2 上使 15-worker thread 吞吐回升 13.65%，且每 handoff 内核指令数 8338→10423（+25.00%）。

## 背景与问题
（承接 <a class="article-ref" href="/lkm/2026/09/23/sched-20260923-001-sched-eevdf-move-to-a-single-runqueue.html">sched-20260923-001</a> → 20261022-007）单运行队列落地 v7.3 后，社区持续追查短任务/`cpu.idle` 场景的尾延迟回退，已分流出 `cpu.idle` 抢占（已修）与 nice 19/short-task 延迟两条线。今日 Chengfeng 把矛头进一步锁定到交付后的一个 DELAY_DEQUEUE 相关 follow-up commit `333238da9a19`（"sched: Update time before requeueing delayed entities"）——Mike Galbraith 在其 wakeup-jitter 测试里点名的对象。该 commit 不是单运行队列本身，但属于其交付后在延迟入队路径上的补丁，疑似引入可测量的吞吐回退。

## 技术方案
（今日为实测数据，非新补丁）Chengfeng 用现成 MMTests recipe 的 `will-it-scale` `context_switch1` 测试（非合成负载）：每个 worker 与自己的 helper 经两条 pipe 交换 1 字节消息，往返计两次 handoff，固定 CORE 亲和到 i7-12700KF 八颗 P-core（每 core 两逻辑 CPU 可用，超 8 worker 后 core 复用），SCHED_OTHER/nice 0、无额外 CPU 竞争者。每次 boot 一次 warmup + 9 次测量，每次 15s 有效测量，GCC 15.2.0、full preemption、powersave governor、balance_performance EPP、Turbo。关键数据（相对两基线均值）：

- 1/2/4/6/8 worker：thread -0.70%..-4.52%、process -1.32%..-4.59%
- 11 worker：-10.54% / -9.96%；15 worker：-15.69% / -14.82%；20 worker：-14.81% / -14.43%
- 26/33/39/40 worker：回退 6.46%..13.55%

15 worker 绝对值：10,875,243 → 9,168,152 → 10,872,945 handoffs/s。单独 revert `333238da9a19` 在 v7.2 上：15-worker 9,413,892 → 10,695,877（+1.28M handoffs/s），2-worker 控制组基本不变。PMU 数据：15-worker 每 handoff 内核指令 8338 → 10423（+25.00%），revert 后 10423 → 8355；two 组对照中上下文切换均约每 handoff 一次。

## 版本演进与当前进展
*current_version: v3（上版日期 2026-10-22；本日为追加实测数据）*。无新补丁。进展集中在把回退归因从「单运行队列本身」细化到交付后的 `333238da9a19` commit，并给出可复现的吞吐/指令数证据链。

## Maintainer 意见与讨论焦点
当日无维护者回复（Chengfeng 致信 Vincent、Mike、Peter，尚未见回应）。Chengfeng 的首封报告漏了 reply headers，随后补发（211476）并给出 openwall 链接 https://lists.openwall.net/linux-kernel/2026/10/30/1506 以挂回 Mike 的线程。此前的既有分歧（nice 19 是否应靠显式 slice 解决）仍无定论，今日数据将「是否 revert/修正 `333238da9a19`」变成一个具体、可量化的待决项。

## 合入评估
*likelihood=medium*。今日给出了针对单 commit 的高质量回退证据（+25% 内核指令、13.65% 吞吐回退），使「修正或 revert `333238da9a19`」成为有数据支撑的具体结论，合入概率上升；但仍需 Michael Ellerman/Mike/Vincent 等确认该数据与既有结论的一致性，以及区分「修正 DELAY_DEQUEUE 相关时间更新」与「回退单运行队列整体」两条路线。*blocking_issues*：需维护者 review 该 commit 的时间更新语义；与 nice 19/short-task 既有回退的关系未理清。*next_action*：等维护者对 `333238da9a19` 数据的回应，决定 fix 还是 revert。

## 效果评估
有具体数字（见「技术方案」节）：15-worker 吞吐 -15.69%（thread）/ -14.82%（process）、revert +13.65%、每 handoff 内核指令 +25.00%；CV ≤2.01%、两基线均值差异 ≤1.39%，数据质量高。

## 我可以参与的点
- **testing**：在其它平台（arm64/AMD）复跑该 `will-it-scale` pipe-handoff recipe，验证 `333238da9a19` 的回退是否平台相关还是普适，并把结果回帖。
- **review**：分析 `333238da9a19`（Update time before requeueing delayed entities）对 DELAY_DEQUEUE 时间记账的影响，判断是修正还是 revert 更合适。

## 参考链接
- lore thread（单运行队列讨论）: https://lore.kernel.org/all/40443762033546b89044587f40b21018971a9867.camel@gmx.de/
- Chengfeng 今日报告（补发链接，正文提供）: https://lists.openwall.net/linux-kernel/2026/10/30/1506
