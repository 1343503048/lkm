---
id: sched-20261105-007
date: 2026-11-05
subject: 'sched/fair: Replace random newidle_balance with Bresenham accumulator'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20261030091946.2498870-1-wangqing7171@gmail.com>
lore_url: https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/
authors:
- Qing Wang
maintainers_involved: []
current_version: v4
patch_series:
- version: v4
  msgid: <20261030091946.2498870-1-wangqing7171@gmail.com>
  date: 2026-10-30
  summary: 用 Bresenham 累加器替换随机 newidle_balance，v4 不再清零 newidle_window_pos。
  review_outcome: Qing 承认 uniform 初值同步问题，提出差异化初值；Chengfeng 测出 2% 吞吐提升。
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: medium
  blocking_issues:
  - uniform 初值的同步问题需差异化初值方案确认
  - 2% 温和收益是否证明复杂度价值待定
  next_action: 给出差异化初值版并附多档位吞吐对比，等 Peter 复核
contribution_opportunities:
- kind: testing
  description: 在生产型负载上测 v4 的延迟尾部与多 sd 同步情况
- kind: review
  description: 审视差异化初值在异构拓扑下是否仍会同步触发
generated_at: '2026-11-06T09:00:00+08:00'
source_email_count: 2
related_articles: []
tags:
- cfs
- idle
- perf
title: 'sched/fair: Replace random newidle_balance with Bresenham accumulator'
layout: article
---

## TL;DR

Qing Wang 的 v4 补丁用 Bresenham 累加器替换 `newidle_balance` 的随机（NI_RANDOM）触发，把「是否做 idle 平衡」变成确定性计数。今日 Qing 与 Peter 就 `newidle_window_pos` 初值展开讨论（v4 已通过「不清零位置」修掉历史丢调用问题），Chengfeng Lin 给出原生 MMTests sembench 数据：815 worker 吞吐提升约 2%，显著低于此前「直接禁用 NI_RANDOM」的诊断对比。补丁已迭代四版但收益偏温和、初值语义仍在收敛。

## 背景与问题

`newidle_balance` 原本用随机方式（`NI_RANDOM`）决定是否在 CPU 进入 idle 时做负载均衡，以避免所有 CPU 同时均衡造成的同步/抖动。但随机引入不确定性，且作者与 Peter 此前讨论过「反复向下取整导致的丢调用」问题。作者目标是换成确定性的 Bresenham 累加器：按每个调度域的权重逐步累加，达到窗口阈值才触发一次均衡，长周期内调用次数精确。

## 技术方案

用 `newidle_window_pos` 累加器取代随机：每轮累加权重、达到 1024 时触发一次并扣减，位置不清零，因此长期均衡次数为 `floor((initial_pos + total_accumulated_weight) / 1024)`，长周期计数精确。今日讨论焦点是初值：Qing 承认「uniform（各 sd 同初值）与 random 等价」的说法应改为「差异有界」，并承认 uniform 版本可能遇到 Peter 指出的同步问题，提出按 per-sd 差异化初值缓解（`.newidle_window_pos = (cpu * 1024) / cpumask_weight(cpu_map)`），使每窗口的偏差成为唯一残余。

## 版本演进与当前进展

*current_version: v4*。v4 关键改动：不再清零 `newidle_window_pos`，从而修掉「反复向下取整丢调用」的历史问题。今日无新版本；Qing 就 sd_init 初值问题进一步澄清并给出差异化初值建议，Chengfeng Lin 补充 v4 的原生测试数据。

## Maintainer 意见与讨论焦点

Peter Zijlstra 的历史意见（今日邮件中引用、未直接回帖）：uniform 初值会让多个 sd 同步触发均衡，存在同步问题。今日 Qing 承认此前「uniform 与 random 等价」的表述过于乐观、应为「差异有界」，并接受差异化初值的缓解方向。尚无对差异化初值方案的最终裁决。

## 合入评估

*likelihood=medium*。补丁已迭代四版、测试数据齐备、作者积极回应 Peter 的同步担忧，但收益偏温和（2%，远低于禁用 NI_RANDOM 的诊断基线），且初值方案尚未得到 Peter 最终认可。*blocking_issues*：① uniform 初值的同步问题需差异化初值确认；② 温和收益是否足以证明复杂度价值待定。*next_action*：作者给出差异化初值版并附多 worker 档位的吞吐对比，等 Peter 复核。

## 效果评估

Chengfeng Lin 在 i7-12700KF（20 逻辑 CPU，含 SMT + E-core）上用原生 MMTests sembench（sembench-ng@26350892f66d，`gcc -O2 -g`）测试：v4 在 815 worker 档位吞吐提升约 2%，「远低于此前诊断中禁用 NI_RANDOM 的改进幅度」。该数字为当前唯一量化证据，且只覆盖 futex 微基准的少量档位。

## 我可以参与的点

- testing：在更贴近生产的工作负载（非 futex 微基准）上测 v4，评估确定性 idle 均衡对延迟尾部分布的影响，尤其关注多 sd 同步问题是否真被差异化初值消除。
- review：审视差异化初值 `(cpu * 1024) / cpumask_weight(cpu_map)` 在异构（大核/E 核）拓扑下是否仍会同步触发。

## 参考链接

- lore thread（v4 补丁）: https://lore.kernel.org/all/20261030091946.2498870-1-wangqing7171@gmail.com/
- Chengfeng 测试数据回帖: https://lore.kernel.org/all/179386941645.8.3608399700168338187.sembench-newidle-v4@gmail.com/
