---
id: sched-20260921-001
date: '2026-09-21'
subject: Improving latency of short slice tasks
subsystem: sched
type: feature
status: rfc
severity: none
thread_root_msgid: <20260921152238.3804392-1-vincent.guittot@linaro.org>
lore_url: https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/
authors:
- Vincent Guittot
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260921152238.3804392-1-vincent.guittot@linaro.org>
  date: '2026-09-21'
  summary: 8 个补丁修复 EEVDF min slice corner case 并新增基于 min slice 的 CPU 选择/wake_affine
    层级
  review_outcome: v1 刚发出，暂无 review 意见
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等待社区 review，关注 min slice 语义改动是否在其他负载引入回归
contribution_opportunities: []
generated_at: '2026-09-22T01:10:00'
source_email_count: 9
related_articles: []
tags:
- eevdf
- cfs
- load_balance
- perf
title: Improving latency of short slice tasks
layout: article
---

## TL;DR
Vincent Guittot 发出新一轮 EEVDF 短 slice 任务延迟优化系列（v1，共 8 个补丁，全部落在 `kernel/sched/fair.c`），修复 min slice 相关的若干 corner case 并首次在多短 slice 任务并发场景下做 CPU 选择优化。cyclictest 99.9 分位与最大延迟显著下降（最大延迟最高 -55%），hackbench pipe 意外获得 +8%~+30% 吞吐提升。v1 刚发出，尚无 review，值得关注后续版本演进。

## 背景与问题
这是 Vincent Guittot 对 EEVDF 短 slice 任务调度延迟的又一轮改进，动机是"fix some remaining corner cases and start to fix some cases when multi short slice tasks are running simultaneously on the system"（修正剩余 corner case，并开始处理多个短 slice 任务同时在系统上运行的场景）。

具体要解决的几类问题：
- `set_protect_slice()` 中 `ineligible_vruntime()` 可能超过一个 min slice 的时长，导致 current 任务实际运行超过一个 min slice（patch 1）。
- `update_protect_slice()` 与 `set_protect_slice()` 逻辑不一致（patch 2）。
- 多个短 slice 任务同时唤醒时处理不当（patch 3、patch 5）。
- 睡眠实体在睡眠期间不会衰减其正 lag，导致任务"永久"持有正 lag（patch 4）。
- CPU 选择（`select_task_rq_fair` 与 `wake_affine`）阶段没有考虑 min slice，短 slice 任务可能被放到会先运行长 slice 任务的 CPU 上（patch 6/7/8）。

## 技术方案
全部改动集中在 `kernel/sched/fair.c`，共 174 行变更（159 增 / 15 删），按序递进：

1. **Ensure that vprot will never go above a min slice**：在 `set_protect_slice()` 中无条件先做 `vprot = min_vruntime(vprot, se->vruntime + calc_delta_fair(slice, se))`，再视 `PREEMPT_SHORT` 特性决定是否进一步取 `ineligible_vruntime()`，保证 current 不会跑超过一个 min slice。
2. **Align update_protect_slice to set_protect_slice**：让更新路径与设置路径用同一套逻辑，并去掉 `ineligible_vruntime()` 中已不成立的 `WARN_ON_ONCE(!curr)`。
3. **Handle more short slice waking cases**：`set_short_buddy()` 在 `cfs_rq->next` 与唤醒实体 slice 相等时，额外用 `entity_before()` 判断先后，避免相等 slice 时的选择偏置。
4. **Decay positive lag of sleeping entities**：新增 `decay_entity_lag()`，用睡眠时长与实体权重在唤醒时衰减正 lag，对称于 delayed dequeue 对负 lag 的处理。**cover letter 明确指出这是带来大部分性能提升的补丁**。
5. **Reset lag when waking up on idle cpu**：多个任务同时唤醒到空闲 CPU 时，最终 vlag 会依赖入队顺序（先入队的丢失 lag，后入队的不丢）。改为在"尚无 fair 任务被 pick 且设为 running"的入队场景下重置 lag，消除顺序依赖。
6. **Add per cpu cached min_slice**：引入 `DEFINE_PER_CPU(u64, rq_min_slice)` 及其更新/读取函数，在任务入队/出队后按需更新缓存值（含 current），供 CPU 选择使用。
7. **Compare min slice during wake_affine**：在 wake_affine 中新增一层 `wake_affine_slice()`，检查唤醒 CPU 是否会因为自身 slice 更长而被抢占。
8. **Add min slice check when selecting CPU**：在 `select_task_rq_fair()` 找不到空闲 CPU 时新增最后一层 `select_slice_cpu()`，比较 slice 来选择"任务能最先运行"的 CPU，避免放到已运行同长或更短 slice 任务的 CPU 上。

## 版本演进与当前进展
v1 刚发出（2026-09-21），尚无 review 意见。系列基于 `tip/sched/core`，测试用默认 2.8ms slice 跑了回归检查，未发现性能回退。

## Maintainer 意见与讨论焦点
作者本人即 sched/eevdf 的核心维护者，v1 发出当日（09-21）无其他维护者回复。系列关注点在于 min slice 语义的改动是否会在其他负载（尤其长 slice / 突发负载）引入回归，需等社区 review。

## 合入评估
likelihood=unknown。这是维护者自研的延迟优化系列，方向（短 slice 任务延迟）与既有 EEVDF 工作一脉相承，但 v1 尚无任何 reviewer 表态，具体合入走向取决于后续 review 与可能出现的争议点，现阶段证据不足以判断。

## 效果评估
cover letter 给出 dragonboard rb5 上三组测试（130s 每组）：
- cyclictest（3777us 周期、8ms slice）：99 分位 91→90（+1%），99.9 分位 126→108（+14%），最大延迟 2273→1018（+55%）。
- cyclictest + rt-app（8/16ms slice）：99.9 分位 1104→832（+25%），最大延迟 6165→3041（+51%）。
- cyclictest + hackbench（8/16ms slice）：99.9 分位 730→637（+13%），最大延迟 15996→8124（+49%）。
- hackbench pipe（默认 2.8ms slice）意外获得提升：process 1/4/8/16 group 分别 +11%/+22%/+25%/+21%，thread 组 +12%/+27%/+30%/+21%。作者明确说 `Decay positive lag of sleeping entities` 是主要贡献者。

## 我可以参与的点
当前阶段暂无明显参与空间（v1 刚发出，尚无 review），可持续观察后续版本。若有 arm64 或异构平台，可考虑在 v2 出现后帮忙复跑 cyclictest/hackbench 并回帖数据，验证 min slice 改动在非 x86 平台上的延迟表现。

## 参考链接
- lore thread: https://lore.kernel.org/all/20260921152238.3804392-1-vincent.guittot@linaro.org/
