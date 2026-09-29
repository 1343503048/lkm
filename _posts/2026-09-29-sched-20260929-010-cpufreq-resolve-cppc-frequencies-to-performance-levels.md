---
id: sched-20260929-010
date: '2026-09-29'
subject: 'cpufreq: Resolve CPPC frequencies to performance levels'
subsystem: sched
type: feature
status: under_review
severity: none
thread_root_msgid: <20260929102957.2591657-1-christian.loehle@arm.com>
lore_url: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/
authors:
- Christian Loehle
maintainers_involved: []
current_version: v1
patch_series:
- version: v1
  msgid: <20260929102957.2591657-1-christian.loehle@arm.com>
  date: '2026-09-29'
  summary: 新增 ->resolve_freq() 回调；CPPC 预计算仿射转换解析频率到 performance level；schedutil 在
    limits 未变时跳过冗余回调
  review_outcome: 无回帖
upstream_commit: null
fixes_commit: null
merged_branch: null
merge_assessment:
  likelihood: unknown
  blocking_issues: []
  next_action: 等 cpufreq 维护者与 schedutil 侧 review
contribution_opportunities:
- kind: review
  description: 核对 resolve_freq 舍入反转、limits 反序取 max、release/acquire 保序的正确性
- kind: testing
  description: 在其它 CPPC/amd-pstate frequency 路径复测 schbench p99 与 set_perf 调用量下降
generated_at: '2026-09-30T01:15:00'
source_email_count: 4
related_articles: []
tags:
- cpufreq
title: 'cpufreq: Resolve CPPC frequencies to performance levels'
layout: article
---

> **subject**：`cpufreq: Resolve CPPC frequencies to performance levels`

## TL;DR

Christian Loehle 的 3 补丁系列：无频率表的 cppc-cpufreq 缺少「频率→性能级」的解析，内核会原样返回请求的 kHz，即使固件只暴露少数几个 CPPC performance level，不同 kHz 请求会miss schedutil 的缓存却写同一个 Desired Performance 值。系列新增 `->resolve_freq()` 回调让 table-less 的 `->target()` 驱动规范化请求，CPPC 预计算仿射转换做解析，并让 schedutil 在「limits 未变」时跳过冗余回调。实测 schbench 平均 p99 降 10%、`cppc_set_perf()` 调用降 23.8%。

## 背景与问题

基于频率表的 cpufreq 驱动会在交给 governor 前把请求解析到频率表条目，不同 kHz 请求选了同一条目就不必再打给驱动。而 table-less 的 cppc-cpufreq 缺这一步：内核返回请求的 kHz 值本身，即使固件只暴露少数 CPPC performance level（测试的 ARM AGI CPU 仅 61 级），不同请求会 miss 掉 schedutil 的频率缓存、却最终写同一个 Desired Performance 值，造成大量冗余的 `cppc_set_perf()` 调用。

## 技术方案

三片补丁：

1. **`cpufreq: Add a driver frequency resolution callback`**：给 table-less 的 `->target()` 驱动新增 `->resolve_freq()`，在给定 limits 内用 `CPUFREQ_RELATION_{L,H,C}` 规范化请求，并文档化回调与校验契约，使调用方能安全缓存解析后的请求。
2. **`cpufreq: CPPC: Resolve frequencies to performance levels`**：CPPC 实现 `->resolve_freq()`，预计算仿射转换并直接反转其整数舍入，与 `->target()`/`->fast_switch()` 共享有界转换；多个 kHz 共享一个 performance level 时选第一个；从每个 policy 快照重算 limits 避免缓存 sysfs 可变控制；nominal 及以下的区间封顶在 Nominal Performance、排除别名的 boost level；limits 在钳到 CPU limits 后 snap 到支持频率。
3. **`cpufreq: Skip updates for unchanged resolved limits`**：让 schedutil 只在「resolved policy->{min,max} 变化仍 pending」时才强制同频回调；快慢回调前都消费 pending 态、用 release/acquire 保序、失败恢复 pending 以支持重试；lockless 读到反序 limits 时取最大值。适用 cppc-cpufreq 与 amd-pstate 的 frequency-based 路径，`->adjust_perf()` 路径不变。

规模：6 文件 +359/−50（含 `kernel/sched/cpufreq_schedutil.c` +19 变更）。

## 版本演进与当前进展

v1 刚发出（cover `<20260929102957.2591657-1-christian.loehle@arm.com>`），当日无回帖。

## Maintainer 意见与讨论焦点

当日无回帖，无维护者表态。

## 合入评估

*likelihood=unknown*。方案完整、自带端到端 benchmark 与 `cppc_set_perf()` 调用量下降数据、且直接改善 schedutil 在 CPPC 上的行为；但刚发出、无 review，且改动横跨 cpufreq core + CPPC 驱动 + schedutil，需要 Rafael/Viresh 与 schedutil 侧确认。*blocking_issues*：无 review。*next_action*：等 cpufreq 维护者（Rafael/Viresh）与 schedutil 侧 review。

## 效果评估

作者在 ARM AGI CPU（61 级 CPPC level）+ schedutil 下跑 `schbench -m 2 -t 31 -F 256 -n 5 -R 18000 -r 60 -w 20 -i 60`（16 轮）：median p99 3364→3280 us（−2.5%）、mean of run p99 3664.2→3299.0 us（−10.0%）、worst run p99 4360→3500 us（−19.7%）、median throughput 16431.08→16460.69 RPS（+0.2%）；同一负载的 instrumented 跑法里 `cppc_set_perf()` 调用 1,136,868→866,703（−23.8%）。

## 我可以参与的点

- `review`：核对 `->resolve_freq()` 的整数舍入反转、`cpufreq_read_policy_limits()` 的「反序取 max」在并发下的正确性，以及 release/acquire 保序是否覆盖 fast_switch 路径。
- `testing`：在其它 CPPC 平台（或 amd-pstate frequency-based 路径）复测 schbench p99 与 `set_perf()` 调用量下降，扩大数据面。

## 参考链接

- lore（cover）: https://lore.kernel.org/all/20260929102957.2591657-1-christian.loehle@arm.com/
- lore（3/3）: https://lore.kernel.org/all/20260929102957.2591657-4-christian.loehle@arm.com/
